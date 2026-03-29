"""
_fracture_base.py — FRACTURE REPAIR shared logic
==================================================

Base class for arm and leg fracture repair minigames.
A drill moves horizontally across the screen. Player presses SPACE or clicks
when the drill is centred over a screw hole to place a screw.

4 screws must be placed IN ORDER from LEFT TO RIGHT. Each hole has a tolerance window:
  PERFECT  (within PERFECT_TOL px): full accuracy score, green flash
  GOOD     (within GOOD_TOL px):    partial accuracy, yellow flash
  MISS     (outside GOOD_TOL):      failed screw, red flash — one miss = FAIL

Subclasses override:
  _draw_limb(surface) — draws the bone X-ray with hand or foot attachment
  REGION_LABEL        — string shown top-right ("ARM" or "LEG")
"""

import pygame
import math
import random
import sys
from .base import BaseMinigame

# ── Palette ───────────────────────────────────────────────────────────────
BG_XRAY         = (10,  14,  22)     # dark blue-black — X-ray feel
GRID_COL        = (14,  18,  28)
BONE_COL        = (195, 210, 225)    # pale bone white
BONE_SHADOW     = (140, 155, 175)
BONE_HIGHLIGHT  = (230, 240, 250)
FRACTURE_COL    = (60,  70,  90)     # dark gap at fracture site
MARROW_COL      = (155, 168, 185)    # inner marrow channel
SCREW_HOLE_IDLE = (80,  90,  110)    # unfilled screw hole
SCREW_HOLE_ACT  = (148, 148, 72)     # active target hole (pulsing)
SCREW_PLACED    = (180, 180, 80)     # placed screw
SCREW_THREAD    = (130, 130, 55)
DRILL_COL       = (160, 170, 155)    # drill body
DRILL_BIT_COL   = (200, 210, 190)
DRILL_TIP_COL   = (220, 220, 100)    # tip glint
PERFECT_COL     = (60,  220, 100)
GOOD_COL        = (200, 190, 60)
MISS_COL        = (200, 50,  50)
TEXT_COL        = (160, 160, 150)
MUTED_COL       = (80,  80,  70)
ACCENT_COL      = (148, 148, 72)
ACC_BAR         = (60,  200, 80)     # accuracy bar fill
ACC_MED         = (200, 160, 40)
ACC_BAD         = (180, 50,  40)
DIM             = (0,   0,   0,  160)

# ── Shared constants ──────────────────────────────────────────────────────
TOTAL_SCREWS    = 4
PERFECT_TOL     = 10    # px either side of hole centre = perfect
GOOD_TOL        = 26    # px either side = good (still passes)
DRILL_SPEED_BASE = 220  # px per second base speed
AUTO_PROCEED_MS = 2600  # ms to show result before auto-returning

# Bone geometry (fractions of screen)
BONE_Y_FRAC     = 0.48   # vertical centre of the bone
BONE_H          = 52     # bone height in pixels
BONE_X_START    = 0.08   # fraction of W where bone starts
BONE_X_END      = 0.92   # fraction of W where bone ends
FRACTURE_W      = 28     # width of the fracture gap in px

# Screw hole positions along the bone (fraction of bone length)
# LEFT TO RIGHT order
SCREW_FRACS     = [0.22, 0.38, 0.62, 0.78]

# Drill dimensions
DRILL_W         = 32
DRILL_H         = 80
DRILL_Y_OFFSET  = -110   # above bone centre


class TypewriterText:
    """Animated text that reveals letters left to right"""
    
    def __init__(self, text, font, color, speed=25):
        self.full_text = text
        self.font = font
        self.color = color
        self.speed = speed
        self.elapsed = 0.0
        self.complete = False
        
    def update(self, dt):
        if not self.complete:
            self.elapsed += dt
            if self.elapsed * self.speed >= len(self.full_text):
                self.complete = True
    
    def get_text(self):
        if self.complete:
            return self.full_text
        return self.full_text[:int(self.elapsed * self.speed)]
    
    def is_complete(self):
        return self.complete
    
    def draw(self, surf, x, y, center_x=False, center_y=False):
        text = self.get_text()
        rendered = self.font.render(text, True, self.color)
        if center_x:
            x = x - rendered.get_width() // 2
        if center_y:
            y = y - rendered.get_height() // 2
        surf.blit(rendered, (x, y))


class FractureRepairBase(BaseMinigame):
    """
    Shared fracture repair logic. Subclass and override
    _draw_limb() and set REGION_LABEL.
    """

    REGION_LABEL = "LIMB"   # override in subclass

    def __init__(self, screen, fonts, patient, region=None):
        super().__init__(screen, fonts, patient, region)
        self.W, self.H = screen.get_size()

        severity = patient.get("severity", 5)
        # Higher severity = faster drill
        self._speed_mult = 1.0 + (severity - 1) * 0.10   # 1.0 – 1.9×

        # Bone geometry in screen coords
        self._bone_y  = int(self.H * BONE_Y_FRAC)
        self._bone_x0 = int(self.W * BONE_X_START)
        self._bone_x1 = int(self.W * BONE_X_END)
        self._bone_len = self._bone_x1 - self._bone_x0

        # Fracture centre
        self._frac_cx = self._bone_x0 + self._bone_len // 2

        # Screw hole positions (LEFT TO RIGHT)
        self._holes = [
            self._bone_x0 + int(f * self._bone_len)
            for f in SCREW_FRACS
        ]

        # State
        self._screws_placed  = []    # list of (x, quality) for placed screws
        self._current_target = 0     # index into self._holes (starts at 0 = leftmost)
        self._drill_x        = float(self._bone_x0)
        self._drill_dir      = 1     # +1 right, -1 left
        self._drill_speed    = DRILL_SPEED_BASE * self._speed_mult
        self._accuracy_score = 100   # starts at 100, drops on poor placements
        self._flash_timer    = 0.0
        self._flash_col      = PERFECT_COL
        self._flash_x        = 0
        self._shake_timer    = 0.0   # screen shake on miss
        self.game_result = None
        self._failure_reason = None  # Store failure reason for display

        # Animation states
        self.anim_state = None
        self.title_anim = None
        self.title_color = None
        self.title_text = None
        self.subtitle_text = ""
        self.return_anim = None
        self.continue_prompt_visible = False
        self.fade_alpha = 255
        self.fade_target = 255
        self.fade_speed = 300
        self.waiting_for_continue = False
        self.auto_continue_timer = 0
        self.auto_continue_delay = 20000
        self.title_complete = False
        self.result_start_time = 0

        # Fade in
        self._game_fade_alpha = 255
        self._fade_surf = pygame.Surface((self.W, self.H))
        self._fade_surf.fill((0, 0, 0))

    # ── Main loop ─────────────────────────────────────────────────────────

    def run(self) -> bool:
        clock = pygame.time.Clock()
        self.anim_state = None
        self.waiting_for_continue = False
        self.auto_continue_timer = 0
        self.title_complete = False
        self.result_start_time = 0

        while True:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # Handle continue key press during result screen
                if self.waiting_for_continue:
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.anim_state == "subtitle":
                            self.anim_state = "fade_out"
                            self.fade_target = 0
                            self.waiting_for_continue = False
                            self.continue_prompt_visible = False
                            print(f"[FractureRepair] Continue pressed. Fading to black.")
                        elif self.anim_state == "return_text":
                            print(f"[FractureRepair] Final continue pressed. Returning result: {self.game_result}")
                            return self.game_result

                # Game input during gameplay
                if not self.anim_state and self.game_result is None:
                    triggered = (
                        (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or
                        (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
                    )
                    if triggered:
                        self._attempt_placement()

            # Update game logic
            if self.game_result is None:
                self._update_game(dt)
            
            # Start result screen when game ends
            if self.game_result is not None and not self.anim_state:
                self.anim_state = "title"
                self._setup_title_animation()
                self.title_complete = False
                self.result_start_time = pygame.time.get_ticks()
                print(f"[FractureRepair] Result={self.game_result}. Starting title animation.")

            # Update fade effect
            if self.fade_alpha != self.fade_target:
                diff = self.fade_target - self.fade_alpha
                change = self.fade_speed * dt
                if abs(diff) <= change:
                    self.fade_alpha = self.fade_target
                else:
                    self.fade_alpha += change if diff > 0 else -change
                self.fade_alpha = max(0, min(255, self.fade_alpha))

            # Update title animation
            if self.anim_state == "title" and self.title_anim:
                self.title_anim.update(dt)
                if self.title_anim.is_complete() and not self.title_complete:
                    self.title_complete = True
                    self.anim_state = "subtitle"
                    self._setup_subtitle()
                    print(f"[FractureRepair] Title complete. Showing subtitle.")
            
            # Update return text animation
            if self.anim_state == "return_text" and self.return_anim:
                self.return_anim.update(dt)
                if self.return_anim.is_complete():
                    self.waiting_for_continue = True
                    self.continue_prompt_visible = True
                    self.auto_continue_timer = pygame.time.get_ticks()
                    print(f"[FractureRepair] Return text complete. Waiting for continue.")
            
            # Auto-continue timer for subtitle screen
            if self.anim_state == "subtitle" and self.waiting_for_continue:
                if pygame.time.get_ticks() - self.auto_continue_timer >= self.auto_continue_delay:
                    self.anim_state = "fade_out"
                    self.fade_target = 0
                    self.waiting_for_continue = False
                    self.continue_prompt_visible = False
                    print(f"[FractureRepair] Auto-advance after 20 seconds. Fading to black.")
            
            # Auto-continue timer for return text screen
            if self.anim_state == "return_text" and self.waiting_for_continue:
                if pygame.time.get_ticks() - self.auto_continue_timer >= self.auto_continue_delay:
                    print(f"[FractureRepair] Auto-advance after 20 seconds. Returning result: {self.game_result}")
                    return self.game_result

            self._draw()
            pygame.display.flip()

    def _setup_title_animation(self):
        """Setup the animated title"""
        if self.game_result:
            self.title_text = "PATIENT STABILIZED"
            self.title_color = (60, 200, 80)
        else:
            self.title_text = "COMPLICATIONS OCCURRED"
            self.title_color = (180, 40, 40)
        
        self.title_anim = TypewriterText(
            self.title_text,
            self.fonts['xlarge'],
            self.title_color,
            speed=20
        )
        self.fade_alpha = 255
        self.fade_target = 255

    def _setup_subtitle(self):
        """Setup the subtitle text (no animation)"""
        if self.game_result:
            self.subtitle_text = "You feel proud, yet you may not rest. There are still other patients waiting for you."
        else:
            self.subtitle_text = "A difficult outcome. You carry the weight. Yet there are still other patients waiting for you."
        
        self.waiting_for_continue = True
        self.continue_prompt_visible = True
        self.auto_continue_timer = pygame.time.get_ticks()

    def _setup_return_text(self):
        """Setup the return text animation after fade"""
        self.return_anim = TypewriterText(
            "You return to the emergency ward",
            self.fonts['large'],
            (148, 148, 72),
            speed=22
        )
        self.fade_target = 255

    def _update_game(self, dt):
        """Update game logic"""
        if self._game_fade_alpha > 0:
            self._game_fade_alpha = max(0, self._game_fade_alpha - 320 * dt)

        # Bounce drill left-right
        self._drill_x += self._drill_dir * self._drill_speed * dt
        if self._drill_x >= self._bone_x1 - DRILL_W // 2:
            self._drill_x = self._bone_x1 - DRILL_W // 2
            self._drill_dir = -1
        elif self._drill_x <= self._bone_x0 + DRILL_W // 2:
            self._drill_x = self._bone_x0 + DRILL_W // 2
            self._drill_dir = 1

        if self._flash_timer > 0:
            self._flash_timer -= dt
        if self._shake_timer > 0:
            self._shake_timer = max(0, self._shake_timer - dt)

    # ── Placement logic ───────────────────────────────────────────────────

    def _attempt_placement(self):
        if self._current_target >= TOTAL_SCREWS:
            return

        target_x = self._holes[self._current_target]
        offset   = abs(int(self._drill_x) - target_x)

        if offset <= PERFECT_TOL:
            quality = 'perfect'
            self._flash_col = PERFECT_COL
            self._accuracy_score = min(100, self._accuracy_score + 5)
        elif offset <= GOOD_TOL:
            quality = 'good'
            self._flash_col = GOOD_COL
            self._accuracy_score = max(0, self._accuracy_score - 10)
        else:
            quality = 'miss'
            self._flash_col = MISS_COL
            self._failure_reason = "You did not match the drill with the correct hole."
            self._accuracy_score = max(0, self._accuracy_score - 35)

        self._flash_timer = 0.55
        self._flash_x     = int(self._drill_x)
        self._screws_placed.append((int(self._drill_x), quality))
        self._current_target += 1

        if quality == 'miss':
            self._shake_timer = 0.35
            self.game_result = False
            return

        # Speed up drill slightly after each screw
        self._drill_speed = min(
            DRILL_SPEED_BASE * self._speed_mult * 1.6,
            self._drill_speed + 18
        )

        if self._current_target >= TOTAL_SCREWS:
            self.game_result = True

    # ── Draw ──────────────────────────────────────────────────────────────

    def _draw(self):
        W, H = self.W, self.H

        # Screen shake offset
        shake = 0
        if self._shake_timer > 0:
            shake = int(math.sin(self._shake_timer * 60) *
                        self._shake_timer * 14)

        self.screen.fill(BG_XRAY)
        self._draw_xray_grid()
        
        # Only draw game elements if not in result animation
        if not self.anim_state:
            self._draw_limb(shake)
            self._draw_screws(shake)
            self._draw_drill(shake)
            self._draw_ui()
            self._draw_accuracy_bar()
            self._draw_left_to_right_instruction()
        else:
            # Draw static game elements dimmed
            self._draw_limb(shake)
            self._draw_screws(shake)
            self._draw_drill(shake)

        if self._game_fade_alpha > 0 and not self.anim_state:
            self._fade_surf.set_alpha(int(self._game_fade_alpha))
            self.screen.blit(self._fade_surf, (0, 0))

        # Draw result overlay
        if self.anim_state:
            # Dark overlay
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            
            # Title animation (stays visible)
            if self.title_anim and self.anim_state in ["title", "subtitle", "fade_out"]:
                title_y = H // 2 - 100
                self.title_anim.draw(self.screen, W // 2, title_y, center_x=True)
            
            # Subtitle (no animation)
            if self.anim_state in ["subtitle", "fade_out"] and self.subtitle_text:
                words = self.subtitle_text.split()
                lines = []
                current_line = []
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    test_surf = self.fonts['medium'].render(test_line, True, TEXT_COL)
                    if test_surf.get_width() <= W - 100:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(' '.join(current_line))
                
                y_offset = H // 2 - 20
                for line in lines:
                    line_surf = self.fonts['medium'].render(line, True, TEXT_COL)
                    line_rect = line_surf.get_rect(center=(W // 2, y_offset))
                    self.screen.blit(line_surf, line_rect)
                    y_offset += 35
            
            # Return text animation (after fade)
            if self.anim_state == "return_text" and self.return_anim:
                self.return_anim.draw(self.screen, W // 2, H // 2, center_x=True)
            
            # Continue prompt
            if self.continue_prompt_visible:
                prompt_text = "Press ENTER to continue"
                prompt_surf = self.fonts['medium'].render(prompt_text, True, MUTED_COL)
                prompt_rect = prompt_surf.get_rect(center=(W // 2, H - 70))
                pulse = abs(math.sin(pygame.time.get_ticks() / 500))
                prompt_surf.set_alpha(int(150 + 105 * pulse))
                self.screen.blit(prompt_surf, prompt_rect)
        
        # Apply fade effect during fade out
        if self.anim_state == "fade_out" and self.fade_alpha < 255:
            fade_overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            fade_overlay.fill((0, 0, 0, int(255 - self.fade_alpha)))
            self.screen.blit(fade_overlay, (0, 0))
            
            if self.fade_alpha == 0:
                self.anim_state = "return_text"
                self._setup_return_text()
                print(f"[FractureRepair] Fade complete. Starting return text.")

    def _draw_xray_grid(self):
        """Faint grid — looks like an X-ray lightbox grid."""
        W, H = self.W, self.H
        for x in range(0, W, 50):
            pygame.draw.line(self.screen, GRID_COL, (x, 0), (x, H))
        for y in range(0, H, 50):
            pygame.draw.line(self.screen, GRID_COL, (0, y), (W, y))

    def _draw_bone_shape(self, surface, shake, col, bdr, highlight):
        """Draw the bone tube — shared by both subclasses."""
        bx0 = self._bone_x0
        bx1 = self._bone_x1
        by  = self._bone_y + shake
        bh  = BONE_H
        r   = bh // 2

        # Main bone tube
        pygame.draw.rect(surface, col,
                         (bx0, by - bh // 2, bx1 - bx0, bh),
                         border_radius=r)
        # Shadow underside
        pygame.draw.rect(surface, bdr,
                         (bx0, by - bh // 2, bx1 - bx0, bh),
                         2, border_radius=r)
        # Highlight top stripe
        pygame.draw.rect(surface, highlight,
                         (bx0 + r, by - bh // 2 + 4, bx1 - bx0 - r * 2, 8),
                         border_radius=3)
        # Marrow channel
        pygame.draw.rect(surface, MARROW_COL,
                         (bx0 + r, by - 6, bx1 - bx0 - r * 2, 12),
                         border_radius=4)

        # Fracture gap — dark crack through the bone
        fcx = self._frac_cx
        fw  = FRACTURE_W
        pygame.draw.rect(surface, FRACTURE_COL,
                         (fcx - fw // 2, by - bh // 2 - 4, fw, bh + 8))
        # Crack lines
        for dx in [-4, 0, 4]:
            pygame.draw.line(surface, (40, 50, 70),
                             (fcx + dx, by - bh // 2 - 6),
                             (fcx + dx + random.randint(-3, 3),
                              by + bh // 2 + 6), 1)

        # Screw hole targets
        for i, hx in enumerate(self._holes):
            placed_here = any(abs(sx - hx) < 20
                              for sx, _ in self._screws_placed)
            is_active   = (i == self._current_target and
                           self.game_result is None and
                           not self.anim_state and
                           not placed_here)

            if is_active:
                # Pulsing effect for active target
                pulse = abs(math.sin(pygame.time.get_ticks() / 200))
                r_col = tuple(int(SCREW_HOLE_ACT[j] * (0.6 + 0.4 * pulse))
                              for j in range(3))
                # Draw glowing ring around active hole
                for rad in range(12, 20, 2):
                    alpha = int(80 * (1 - (rad - 12) / 8))
                    glow = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow, (*SCREW_HOLE_ACT, alpha), (rad, rad), rad)
                    surface.blit(glow, (hx - rad, by - rad))
            else:
                r_col = SCREW_HOLE_IDLE if not placed_here else SCREW_PLACED

            pygame.draw.circle(surface, r_col, (hx, by), 9)
            pygame.draw.circle(surface, (50, 60, 80), (hx, by), 9, 2)

            # Inner hole
            if not placed_here:
                pygame.draw.circle(surface, FRACTURE_COL, (hx, by), 4)
            else:
                # Screw head detail
                pygame.draw.circle(surface, (200, 200, 120), (hx, by), 5)
                pygame.draw.line(surface, (100, 100, 60), (hx - 3, by), (hx + 3, by), 2)
                pygame.draw.line(surface, (100, 100, 60), (hx, by - 3), (hx, by + 3), 2)

            # Number the holes (1-4) for clarity
            if not placed_here and self.game_result is None and not self.anim_state:
                num_s = self.fonts['severity'].render(str(i + 1), True, (100, 110, 130))
                surface.blit(num_s, (hx - 5, by - 18))

    def _draw_limb(self, shake):
        """Override in subclass to draw bone + hand or foot."""
        self._draw_bone_shape(self.screen, shake,
                              BONE_COL, BONE_SHADOW, BONE_HIGHLIGHT)

    def _draw_screws(self, shake):
        """Draw placed screws as titanium bolts through the bone."""
        by = self._bone_y + shake
        for sx, quality in self._screws_placed:
            screw_col = SCREW_PLACED if quality != 'miss' else MISS_COL
            # Shaft
            pygame.draw.rect(self.screen, screw_col,
                             (sx - 4, by - BONE_H // 2 - 8,
                              8, BONE_H + 16))
            # Thread lines
            for ty in range(by - BONE_H // 2, by + BONE_H // 2, 5):
                pygame.draw.line(self.screen, SCREW_THREAD,
                                 (sx - 4, ty), (sx + 4, ty), 1)
            # Head (hexagonal look via two rects)
            pygame.draw.rect(self.screen, SCREW_PLACED,
                             (sx - 8, by - BONE_H // 2 - 18, 16, 10),
                             border_radius=2)
            pygame.draw.rect(self.screen, BONE_HIGHLIGHT,
                             (sx - 6, by - BONE_H // 2 - 17, 12, 4),
                             border_radius=1)

            # Flash overlay
            if self._flash_timer > 0 and abs(sx - self._flash_x) < 20:
                alpha = int(200 * (self._flash_timer / 0.55))
                fsurf = pygame.Surface((20, BONE_H + 24), pygame.SRCALPHA)
                fsurf.fill((*self._flash_col, min(alpha, 180)))
                self.screen.blit(fsurf,
                                 (sx - 10, by - BONE_H // 2 - 4))

    def _draw_drill(self, shake):
        """Draw the moving surgical drill above the bone."""
        if self.anim_state or self.game_result is not None:
            return

        dx = int(self._drill_x)
        dy = self._bone_y + shake + DRILL_Y_OFFSET
        dw = DRILL_W
        dh = DRILL_H

        # Drill body — tapered rectangle
        pygame.draw.rect(self.screen, DRILL_COL,
                         (dx - dw // 2, dy, dw, dh - 20),
                         border_radius=4)
        pygame.draw.rect(self.screen, (120, 130, 118),
                         (dx - dw // 2, dy, dw, dh - 20),
                         1, border_radius=4)

        # Chuck (wider section at top)
        pygame.draw.rect(self.screen, (140, 148, 135),
                         (dx - dw // 2 - 4, dy, dw + 8, 16),
                         border_radius=3)

        # Drill bit (narrower, extending down)
        bit_x = dx - 4
        bit_y = dy + dh - 20
        bit_h = 28
        pygame.draw.rect(self.screen, DRILL_BIT_COL,
                         (bit_x, bit_y, 8, bit_h))

        # Tip glint
        pygame.draw.polygon(self.screen, DRILL_TIP_COL, [
            (bit_x, bit_y + bit_h),
            (bit_x + 4, bit_y + bit_h + 10),
            (bit_x + 8, bit_y + bit_h),
        ])

        # Highlight stripe on drill body
        pygame.draw.rect(self.screen, (180, 190, 175),
                         (dx - dw // 2 + 3, dy + 18, 5, dh - 40))

        # Vertical alignment guide line (faint)
        target_x = self._holes[self._current_target] \
            if self._current_target < TOTAL_SCREWS else dx
        dist  = abs(dx - target_x)
        alpha = max(0, int(180 * (1 - dist / 100)))
        if alpha > 10:
            guide = pygame.Surface((2, self._bone_y + shake - (dy + dh)), pygame.SRCALPHA)
            guide.fill((148, 148, 72, alpha))
            self.screen.blit(guide, (dx - 1, dy + dh))

    def _draw_accuracy_bar(self):
        """Accuracy meter bottom-left."""
        W, H = self.W, self.H
        bar_x = 36
        bar_y = H - 32
        bar_w = 280
        bar_h = 10

        pygame.draw.rect(self.screen, (18, 22, 32), (bar_x, bar_y, bar_w, bar_h))
        ratio    = self._accuracy_score / 100
        fill_col = ACC_BAR if ratio > 0.6 else (ACC_MED if ratio > 0.35 else ACC_BAD)
        fill_w   = int(bar_w * ratio)
        if fill_w > 0:
            pygame.draw.rect(self.screen, fill_col,
                             (bar_x, bar_y, fill_w, bar_h))
        pygame.draw.rect(self.screen, (45, 55, 75),
                         (bar_x, bar_y, bar_w, bar_h), 1)

        lbl = self.fonts['severity'].render(
            f"ACCURACY  {self._accuracy_score}%", True, MUTED_COL)
        self.screen.blit(lbl, (bar_x, bar_y - 16))

    def _draw_left_to_right_instruction(self):
        """Draw clear instruction about left-to-right order"""
        W, H = self.W, self.H
        
        # Only show if game still active
        if self.anim_state or self.game_result is not None:
            return
            
        # Instruction box at top of screen
        instr_text = "PLACE SCREWS IN ORDER: 1 → 2 → 3 → 4 (LEFT TO RIGHT)"
        instr_surf = self.fonts['medium'].render(instr_text, True, ACCENT_COL)
        
        # Background for instruction
        bg_rect = pygame.Rect((W - instr_surf.get_width()) // 2 - 10, 
                              85, 
                              instr_surf.get_width() + 20, 
                              32)
        pygame.draw.rect(self.screen, (0, 0, 0, 150), bg_rect, border_radius=4)
        pygame.draw.rect(self.screen, ACCENT_COL, bg_rect, 1, border_radius=4)
        self.screen.blit(instr_surf, ((W - instr_surf.get_width()) // 2, 92))
        
        # Draw arrow indicators above each hole
        arrow_y = 130
        for i, hx in enumerate(self._holes):
            if i >= self._current_target:
                # Draw arrow pointing to current target
                if i == self._current_target:
                    arrow_col = ACCENT_COL
                    pulse = abs(math.sin(pygame.time.get_ticks() / 300))
                    arrow_col = tuple(int(c * (0.6 + 0.4 * pulse)) for c in arrow_col)
                else:
                    arrow_col = (60, 70, 80)
                
                # Draw arrow
                points = [(hx, arrow_y), (hx - 8, arrow_y + 12), (hx + 8, arrow_y + 12)]
                pygame.draw.polygon(self.screen, arrow_col, points)

    def _draw_ui(self):
        W, H = self.W, self.H
        p    = self.patient

        # Patient header
        self.screen.blit(self.fonts['large'].render(
            f"{p['name']}, {p['age']}", True, TEXT_COL), (36, 20))
        self.screen.blit(self.fonts['small'].render(
            p['condition'], True, MUTED_COL), (36, 48))

        # Region top-right
        reg = self.fonts['small'].render(
            f"OPERATING: {self.REGION_LABEL}", True, ACCENT_COL)
        self.screen.blit(reg, (W - reg.get_width() - 36, 20))

        # Screw progress with current target indicator
        prog_text = f"SCREWS  {len(self._screws_placed)} / {TOTAL_SCREWS}"
        if self._current_target < TOTAL_SCREWS and self.game_result is None and not self.anim_state:
            prog_text += f"  →  NEXT: HOLE {self._current_target + 1}"
        prog = self.fonts['small'].render(prog_text, True, ACCENT_COL if self._current_target < TOTAL_SCREWS else MUTED_COL)
        self.screen.blit(prog, (W - prog.get_width() - 36, 44))

        # Screw progress dots with labels
        dot_x = W - 36 - TOTAL_SCREWS * 28
        dot_y = 66
        for i in range(TOTAL_SCREWS):
            if i < len(self._screws_placed):
                _, q = self._screws_placed[i]
                col  = PERFECT_COL if q == 'perfect' else \
                       GOOD_COL    if q == 'good'    else MISS_COL
            elif i == self._current_target and self.game_result is None and not self.anim_state:
                pulse = abs(math.sin(pygame.time.get_ticks() / 300))
                col   = tuple(int(ACCENT_COL[j] * (0.5 + 0.5 * pulse))
                              for j in range(3))
            else:
                col = (35, 42, 55)
            
            # Draw circle
            pygame.draw.circle(self.screen, col, (dot_x + i * 28 + 10, dot_y), 10)
            pygame.draw.circle(self.screen, (55, 65, 80), (dot_x + i * 28 + 10, dot_y), 10, 1)
            
            # Draw number inside circle
            num_s = self.fonts['severity'].render(str(i + 1), True, (200, 200, 180) if i == self._current_target and self.game_result is None else (100, 100, 100))
            self.screen.blit(num_s, (dot_x + i * 28 + 5, dot_y - 6))

        # Instruction
        if self.game_result is None and not self.anim_state:
            inst = self.fonts['medium'].render(
                "SPACE or CLICK when drill is centred on the glowing hole", True, TEXT_COL)
            self.screen.blit(inst,
                             ((W - inst.get_width()) // 2, H - 70))

        # Flash quality label
        if self._flash_timer > 0:
            labels = {
                id(PERFECT_COL): ("PERFECT", PERFECT_COL),
                id(GOOD_COL):    ("GOOD",    GOOD_COL),
                id(MISS_COL):    ("MISSED",  MISS_COL),
            }
            key = id(self._flash_col)
            if key in labels:
                txt, col = labels[key]
                alpha    = int(255 * min(1.0, self._flash_timer / 0.3))
                q_surf   = self.fonts['large'].render(txt, True, col)
                q_surf.set_alpha(alpha)
                self.screen.blit(
                    q_surf,
                    ((W - q_surf.get_width()) // 2,
                     self._bone_y - BONE_H - 60))