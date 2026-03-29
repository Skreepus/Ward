"""
spine_minigame.py — VERTEBRAE STACK
=====================================

Spinal surgery minigame. A side-view of a spine shows 5 missing vertebrae.
A block swings left-right on a pendulum. Click/SPACE to drop it onto the stack.

Scoring per placement:
  - Perfect (within PERFECT_TOL pixels of centre): +2 stability, block width unchanged
  - Good    (within GOOD_TOL pixels):               +1 stability, block shrinks slightly
  - Poor    (outside GOOD_TOL but lands on stack):  -1 stability, block shrinks more
  - Miss    (lands off the stack entirely):          stack topples → immediate FAIL

Stability starts at 10. Reaching 0 at any point = FAIL.
Stack all 5 = SUCCESS.
"""

import pygame
import math
import random
import sys
from .base import BaseMinigame

# ── Palette ───────────────────────────────────────────────────────────────
BG_COL          = (8,   12,  10)
GRID_COL        = (14,  24,  16)
SPINE_COL       = (45,  55,  50)
SPINE_BDR       = (70,  85,  75)
VERT_EMPTY_COL  = (28,  35,  30)
VERT_EMPTY_BDR  = (55,  70,  60)
VERT_PLACED_COL = (60,  160, 90)
VERT_PLACED_BDR = (80,  200, 110)
VERT_ACTIVE_COL = (148, 148, 72)
SWING_COL       = (148, 148, 72)
SWING_BDR       = (200, 200, 100)
STACK_COL       = (55,  130, 75)
STACK_BDR       = (80,  180, 100)
PERFECT_COL     = (60,  220, 100)
POOR_COL        = (200, 140, 40)
MISS_COL        = (180, 40,  40)
TEXT_COL        = (160, 160, 150)
MUTED_COL       = (80,  80,  70)
ACCENT_COL      = (148, 148, 72)
STAB_GOOD       = (60,  200, 80)
STAB_MED        = (200, 160, 40)
STAB_BAD        = (180, 50,  40)
DIM             = (0,   0,   0,  160)

# ── Constants ─────────────────────────────────────────────────────────────
TOTAL_VERTEBRAE = 5
PERFECT_TOL     = 8
GOOD_TOL        = 22
SWING_SPEED_BASE = 1.8
SWING_AMP       = 160
BLOCK_W_BASE    = 110
BLOCK_H         = 26
BLOCK_SHRINK_GOOD = 0.90
BLOCK_SHRINK_POOR = 0.78


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


class VertebralBlock:
    """A single vertebra block swinging on a pendulum."""

    def __init__(self, cx, y, width, speed):
        self.cx     = cx
        self.y      = y
        self.width  = width
        self.speed  = speed
        self.angle  = -math.pi / 2
        self.placed = False

    def update(self, dt):
        if not self.placed:
            self.angle += self.speed * dt

    @property
    def screen_x(self):
        return int(self.cx + math.sin(self.angle) * SWING_AMP - self.width / 2)

    @property
    def centre_x(self):
        return int(self.cx + math.sin(self.angle) * SWING_AMP)

    def draw(self, surface, col=None, bdr=None):
        col = col or SWING_COL
        bdr = bdr or SWING_BDR
        rx  = self.screen_x
        pygame.draw.rect(surface, col,
                         (rx, self.y, int(self.width), BLOCK_H),
                         border_radius=4)
        pygame.draw.rect(surface, bdr,
                         (rx, self.y, int(self.width), BLOCK_H),
                         1, border_radius=4)

        step = 10
        for i in range(0, int(self.width), step):
            pygame.draw.line(surface, bdr,
                             (rx + i, self.y + 2),
                             (rx + i + 4, self.y + BLOCK_H - 2), 1)


class SpineMinigame(BaseMinigame):
    """
    VERTEBRAE STACK — spinal surgery stacking minigame.
    """

    def __init__(self, screen, fonts, patient, region="spine"):
        super().__init__(screen, fonts, patient, region)
        self.W, self.H = screen.get_size()

        severity = patient.get("severity", 5)
        self._speed_mult = 1.0 + (severity - 1) * 0.08

        # Layout
        self._arena_x     = int(self.W * 0.42)
        self._arena_cx    = int(self.W * 0.71)
        self._arena_w     = self.W - self._arena_x
        self._stack_base_y = int(self.H * 0.82)
        self._block_gap    = BLOCK_H + 6
        self._swing_y      = int(self.H * 0.18)

        # Game state
        self._placed        = []
        self._current_block = None
        self._stability     = 10
        self._max_stability = 10
        self._flash_timer   = 0.0
        self._flash_col     = PERFECT_COL
        self._flash_x       = 0
        self._flash_w       = 0
        self._wobble        = 0.0
        self._topple_timer  = 0.0
        self.game_result    = None

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

        self._spawn_block()

        self._fade_alpha = 255
        self._fade_surf = pygame.Surface((self.W, self.H))
        self._fade_surf.fill((0, 0, 0))

    def _spawn_block(self):
        level = len(self._placed)
        speed = (SWING_SPEED_BASE + level * 0.22) * self._speed_mult
        width = BLOCK_W_BASE

        for _, w, _ in self._placed:
            width = w

        self._current_block = VertebralBlock(
            cx=self._arena_cx,
            y=self._swing_y,
            width=max(28, width),
            speed=speed,
        )

    def _place_block(self):
        block = self._current_block
        level = len(self._placed)

        if level == 0:
            target_cx = self._arena_cx
        else:
            target_cx, _, _ = self._placed[-1]

        offset = abs(block.centre_x - target_cx)

        half_prev_w = (self._placed[-1][1] if self._placed else BLOCK_W_BASE) / 2
        half_curr_w = block.width / 2
        miss = offset > (half_prev_w + half_curr_w - 4)

        if level == 0:
            miss = abs(block.centre_x - self._arena_cx) > BLOCK_W_BASE * 0.8

        if miss:
            return 'miss'

        if offset <= PERFECT_TOL:
            return 'perfect'
        elif offset <= GOOD_TOL:
            return 'good'
        else:
            return 'poor'

    def _apply_placement(self, quality):
        block = self._current_block

        if quality == 'miss':
            self._stability = 0
            self._flash_col = MISS_COL
            self._flash_timer = 0.8
            self._flash_x = block.screen_x
            self._flash_w = int(block.width)
            self._topple_timer = 0.001
            self.game_result = False
            return

        offset = block.centre_x - self._arena_cx if not self._placed else \
                 block.centre_x - self._placed[-1][0]

        new_width = block.width
        if quality == 'perfect':
            self._stability = min(self._max_stability, self._stability + 2)
            self._flash_col = PERFECT_COL
        elif quality == 'good':
            self._stability = min(self._max_stability, self._stability + 1)
            self._flash_col = STAB_GOOD
            new_width = block.width * BLOCK_SHRINK_GOOD
        else:
            self._stability -= 1
            self._flash_col = POOR_COL
            new_width = block.width * BLOCK_SHRINK_POOR
            self._wobble = 1.0

        self._flash_timer = 0.5
        self._flash_x = block.screen_x
        self._flash_w = int(block.width)

        self._placed.append((block.centre_x, new_width, offset))

        if self._stability <= 0:
            self._topple_timer = 0.001
            self.game_result = False
            return

        if len(self._placed) >= TOTAL_VERTEBRAE:
            self.game_result = True
            return

        self._spawn_block()
        self._current_block.width = max(28, new_width)

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
                            print(f"[SpineMinigame] Continue pressed. Fading to black.")
                        elif self.anim_state == "return_text":
                            print(f"[SpineMinigame] Final continue pressed. Returning result: {self.game_result}")
                            return self.game_result
                
                # Game input during gameplay
                if not self.anim_state and self.game_result is None:
                    if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                        key_ok = (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE)
                        click_ok = (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
                        if key_ok or click_ok:
                            quality = self._place_block()
                            self._apply_placement(quality)

            # Update game logic
            if self.game_result is None:
                self._update_game(dt)
            
            # Start result screen when game ends
            if self.game_result is not None and not self.anim_state:
                self.anim_state = "title"
                self._setup_title_animation()
                self.title_complete = False
                self.result_start_time = pygame.time.get_ticks()
                print(f"[SpineMinigame] Result={self.game_result}. Starting title animation.")

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
                    print(f"[SpineMinigame] Title complete. Showing subtitle.")
            
            # Update return text animation
            if self.anim_state == "return_text" and self.return_anim:
                self.return_anim.update(dt)
                if self.return_anim.is_complete():
                    self.waiting_for_continue = True
                    self.continue_prompt_visible = True
                    self.auto_continue_timer = pygame.time.get_ticks()
                    print(f"[SpineMinigame] Return text complete. Waiting for continue.")
            
            # Auto-continue timer for subtitle screen
            if self.anim_state == "subtitle" and self.waiting_for_continue:
                if pygame.time.get_ticks() - self.auto_continue_timer >= self.auto_continue_delay:
                    self.anim_state = "fade_out"
                    self.fade_target = 0
                    self.waiting_for_continue = False
                    self.continue_prompt_visible = False
                    print(f"[SpineMinigame] Auto-advance after 20 seconds. Fading to black.")
            
            # Auto-continue timer for return text screen
            if self.anim_state == "return_text" and self.waiting_for_continue:
                if pygame.time.get_ticks() - self.auto_continue_timer >= self.auto_continue_delay:
                    print(f"[SpineMinigame] Auto-advance after 20 seconds. Returning result: {self.game_result}")
                    return self.game_result

            self._draw()
            pygame.display.flip()

    def _update_game(self, dt):
        """Update game logic"""
        if self._fade_alpha > 0:
            self._fade_alpha = max(0, self._fade_alpha - 320 * dt)

        if self._current_block:
            self._current_block.update(dt)

        if self._flash_timer > 0:
            self._flash_timer -= dt

        if self._wobble > 0:
            self._wobble = max(0, self._wobble - dt * 1.8)

        if self._topple_timer > 0:
            self._topple_timer += dt

    def _draw(self):
        W, H = self.W, self.H
        
        # Always draw the game screen first
        self.screen.fill(BG_COL)
        self._draw_grid()
        
        # Only draw game elements if not in result animation
        if not self.anim_state:
            self._draw_spine_diagram()
            self._draw_arena_bg()
            self._draw_stack()
            self._draw_swing_block()
            self._draw_ui()
            self._draw_stability_bar()
        else:
            # Draw static game elements dimmed
            self._draw_spine_diagram()
            self._draw_arena_bg()
            self._draw_stack()
            self._draw_swing_block()

        if self._fade_alpha > 0 and not self.anim_state:
            self._fade_surf.set_alpha(int(self._fade_alpha))
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
                print(f"[SpineMinigame] Fade complete. Starting return text.")

    def _draw_grid(self):
        W, H = self.W, self.H
        for x in range(0, W, 44):
            pygame.draw.line(self.screen, GRID_COL, (x, 0), (x, H))
        for y in range(0, H, 44):
            pygame.draw.line(self.screen, GRID_COL, (0, y), (W, y))

    def _draw_spine_diagram(self):
        W, H = self.W, self.H
        spine_cx  = int(W * 0.22)
        spine_top = int(H * 0.10)
        spine_bot = int(H * 0.88)
        spine_w   = 22

        pygame.draw.rect(self.screen, SPINE_COL,
                         (spine_cx - spine_w // 2, spine_top,
                          spine_w, spine_bot - spine_top),
                         border_radius=8)
        pygame.draw.rect(self.screen, SPINE_BDR,
                         (spine_cx - spine_w // 2, spine_top,
                          spine_w, spine_bot - spine_top),
                         1, border_radius=8)

        total_span = int((spine_bot - spine_top) * 0.80)
        slot_start = spine_top + int((spine_bot - spine_top) * 0.08)
        slot_gap   = total_span // (TOTAL_VERTEBRAE - 1)
        slot_w     = 64
        slot_h     = 18

        for i in range(TOTAL_VERTEBRAE):
            sy  = slot_start + i * slot_gap - slot_h // 2
            sx  = spine_cx - slot_w // 2

            placed_count = len(self._placed)

            if i < placed_count:
                col = VERT_PLACED_COL
                bdr = VERT_PLACED_BDR
            elif i == placed_count and self.game_result is None and not self.anim_state:
                pulse = abs(math.sin(pygame.time.get_ticks() / 350))
                r = int(VERT_ACTIVE_COL[0] * (0.6 + 0.4 * pulse))
                g = int(VERT_ACTIVE_COL[1] * (0.6 + 0.4 * pulse))
                b = int(VERT_ACTIVE_COL[2] * (0.6 + 0.4 * pulse))
                col = (r, g, b)
                bdr = VERT_PLACED_BDR
            else:
                col = VERT_EMPTY_COL
                bdr = VERT_EMPTY_BDR

            pygame.draw.rect(self.screen, col,
                             (sx, sy, slot_w, slot_h), border_radius=3)
            pygame.draw.rect(self.screen, bdr,
                             (sx, sy, slot_w, slot_h), 1, border_radius=3)

            num_s = self.fonts['severity'].render(str(i + 1), True, bdr)
            self.screen.blit(num_s, (sx + slot_w + 6, sy + 2))

        lbl = self.fonts['small'].render("SPINAL COLUMN", True, MUTED_COL)
        self.screen.blit(lbl, (spine_cx - lbl.get_width() // 2, spine_bot + 12))

    def _draw_arena_bg(self):
        W, H = self.W, self.H
        sep_x = self._arena_x
        pygame.draw.line(self.screen, (30, 40, 34), (sep_x, 0), (sep_x, H), 1)

        lz_w  = int(BLOCK_W_BASE * 1.4)
        lz_x  = self._arena_cx - lz_w // 2
        lz_y  = self._stack_base_y + BLOCK_H + 4
        pygame.draw.rect(self.screen, (20, 36, 24), (lz_x, lz_y, lz_w, 3))

    def _draw_stack(self):
        wobble_offset = int(math.sin(pygame.time.get_ticks() / 80) * self._wobble * 7) if self._wobble > 0 else 0
        topple = self._topple_timer > 0
        topple_t = min(1.0, self._topple_timer / 0.8) if topple else 0

        for i, (cx, w, offset) in enumerate(self._placed):
            bx  = int(cx - w / 2) + wobble_offset
            by  = self._stack_base_y - i * self._block_gap

            if topple:
                spread = int(topple_t * (i + 1) * 18 * (1 if i % 2 == 0 else -1))
                fall   = int(topple_t ** 2 * 80)
                bx    += spread
                by    += fall

            pygame.draw.rect(self.screen, STACK_COL,
                             (bx, by, int(w), BLOCK_H), border_radius=3)
            pygame.draw.rect(self.screen, STACK_BDR,
                             (bx, by, int(w), BLOCK_H), 1, border_radius=3)

            step = 9
            for j in range(0, int(w), step):
                pygame.draw.line(self.screen, STACK_BDR,
                                 (bx + j, by + 2),
                                 (bx + j + 4, by + BLOCK_H - 2), 1)

        if self._flash_timer > 0 and self._placed:
            alpha  = int(200 * (self._flash_timer / 0.5))
            flash_x, flash_w = self._flash_x, self._flash_w
            flash_y  = self._stack_base_y - (len(self._placed) - 1) * self._block_gap
            fsurf    = pygame.Surface((flash_w, BLOCK_H), pygame.SRCALPHA)
            fsurf.fill((*self._flash_col, min(alpha, 180)))
            self.screen.blit(fsurf, (flash_x, flash_y))

    def _draw_swing_block(self):
        if self._current_block is None or self.game_result is not None or self.anim_state:
            return

        block = self._current_block
        cx_screen = self._arena_cx
        pivot_y   = self._swing_y - 30

        pygame.draw.line(self.screen, (40, 55, 45),
                         (cx_screen, pivot_y),
                         (block.centre_x, block.y), 1)

        stack_top_y = self._stack_base_y - len(self._placed) * self._block_gap
        pygame.draw.line(self.screen, (35, 48, 38),
                         (block.centre_x, block.y + BLOCK_H),
                         (block.centre_x, stack_top_y), 1)

        block.draw(self.screen)
        pygame.draw.circle(self.screen, SWING_BDR,
                           (block.centre_x, block.y + BLOCK_H // 2), 3)

    def _draw_stability_bar(self):
        W, H = self.W, self.H
        bar_x  = self._arena_x + 20
        bar_y  = H - 32
        bar_w  = W - self._arena_x - 40
        bar_h  = 10

        pygame.draw.rect(self.screen, (20, 28, 22), (bar_x, bar_y, bar_w, bar_h))

        ratio    = max(0, self._stability / self._max_stability)
        fill_w   = int(bar_w * ratio)
        fill_col = STAB_GOOD if ratio > 0.6 else (STAB_MED if ratio > 0.3 else STAB_BAD)

        if fill_w > 0:
            pygame.draw.rect(self.screen, fill_col, (bar_x, bar_y, fill_w, bar_h))
        pygame.draw.rect(self.screen, (50, 65, 55), (bar_x, bar_y, bar_w, bar_h), 1)

        lbl = self.fonts['severity'].render(f"STABILITY  {self._stability}/{self._max_stability}", True, MUTED_COL)
        self.screen.blit(lbl, (bar_x, bar_y - 16))

    def _draw_ui(self):
        W, H = self.W, self.H
        p = self.patient

        self.screen.blit(self.fonts['large'].render(
            f"{p['name']}, {p['age']}", True, TEXT_COL), (36, 20))
        self.screen.blit(self.fonts['small'].render(
            p['condition'], True, MUTED_COL), (36, 48))

        reg = self.fonts['small'].render("OPERATING: SPINE", True, ACCENT_COL)
        self.screen.blit(reg, (W - reg.get_width() - 36, 20))

        prog = self.fonts['small'].render(
            f"VERTEBRAE  {len(self._placed)} / {TOTAL_VERTEBRAE}", True, MUTED_COL)
        self.screen.blit(prog, (W - prog.get_width() - 36, 44))

        if self.game_result is None:
            inst_text = "SPACE or CLICK to place vertebra"
            inst = self.fonts['medium'].render(inst_text, True, TEXT_COL)
            self.screen.blit(inst, ((W - inst.get_width()) // 2 + 80, H // 2 - 8))

        if self._flash_timer > 0 and self._placed:
            quality_text = ""
            if self._flash_col == PERFECT_COL:
                quality_text = "PERFECT"
                q_col = PERFECT_COL
            elif self._flash_col == STAB_GOOD:
                quality_text = "GOOD"
                q_col = STAB_GOOD
            elif self._flash_col == POOR_COL:
                quality_text = "POOR"
                q_col = POOR_COL
            else:
                quality_text = "MISSED"
                q_col = MISS_COL

            alpha   = int(255 * min(1.0, self._flash_timer / 0.3))
            q_surf  = self.fonts['large'].render(quality_text, True, q_col)
            q_surf.set_alpha(alpha)
            self.screen.blit(q_surf,
                             (self._arena_cx - q_surf.get_width() // 2,
                              self._swing_y + BLOCK_H + 18))