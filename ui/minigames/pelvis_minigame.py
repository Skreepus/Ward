"""
pelvis_minigame.py — BONE ALIGNMENT
====================================

Pelvic fracture repair puzzle minigame.
A target pelvis (top) is in a fixed random orientation.
A rotating pelvis (bottom) spins continuously.
Player must click/SPACE when the rotating pelvis aligns with the target.

3 successful matches required to succeed.
Each miss or incorrect timing adds a penalty and resets the current attempt.
"""

import pygame
import math
import random
import sys
from .base import BaseMinigame

# ── Palette ───────────────────────────────────────────────────────────────
BG_COL          = (10, 14, 22)      # dark medical background
GRID_COL        = (14, 18, 28)
BONE_COL        = (195, 210, 225)   # pale bone white
BONE_SHADOW     = (140, 155, 175)
BONE_HIGHLIGHT  = (230, 240, 250)
JOINT_COL       = (100, 110, 130)
OUTLINE_COL     = (80, 90, 110)
MATCH_GOOD_COL  = (60, 200, 80)
MATCH_POOR_COL  = (200, 160, 40)
MATCH_MISS_COL  = (200, 50, 50)
ALIGNMENT_GOOD  = (100, 220, 120)
TEXT_COL        = (160, 160, 150)
MUTED_COL       = (80, 80, 70)
ACCENT_COL      = (148, 148, 72)
PERFECT_COL     = (60, 220, 100)
GOOD_COL        = (200, 190, 60)
MISS_COL        = (200, 50, 50)
DIM             = (0, 0, 0, 160)


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


class Pelvis:
    """Drawable pelvis bone with rotation"""
    
    def __init__(self, x, y, size=120, color=BONE_COL):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.angle = 0
        self.temp_surface = None
        
    def set_angle(self, angle):
        self.angle = angle % 360
        
    def rotate(self, delta):
        self.angle = (self.angle + delta) % 360
        
    def draw(self, surface, outline_color=OUTLINE_COL, glow=False):
        """Draw the pelvis shape at current angle"""
        # Create a surface for the pelvis
        w = int(self.size * 1.2)
        h = int(self.size * 1.0)
        pelvis_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pelvis_surf.fill((0, 0, 0, 0))
        
        # Draw the pelvic bone shape
        cx, cy = w // 2, h // 2
        r = self.size // 2
        
        # Left iliac wing
        points_left = [
            (cx - r * 0.5, cy - r * 0.8),
            (cx - r * 0.9, cy - r * 0.2),
            (cx - r * 0.8, cy + r * 0.3),
            (cx - r * 0.4, cy + r * 0.4),
            (cx - r * 0.3, cy),
            (cx - r * 0.4, cy - r * 0.5),
        ]
        
        # Right iliac wing
        points_right = [
            (cx + r * 0.5, cy - r * 0.8),
            (cx + r * 0.9, cy - r * 0.2),
            (cx + r * 0.8, cy + r * 0.3),
            (cx + r * 0.4, cy + r * 0.4),
            (cx + r * 0.3, cy),
            (cx + r * 0.4, cy - r * 0.5),
        ]
        
        # Sacrum (center)
        sacrum_points = [
            (cx - r * 0.2, cy + r * 0.1),
            (cx, cy + r * 0.3),
            (cx + r * 0.2, cy + r * 0.1),
            (cx + r * 0.15, cy - r * 0.1),
            (cx, cy - r * 0.2),
            (cx - r * 0.15, cy - r * 0.1),
        ]
        
        # Pubic rami (bottom)
        pubis_points = [
            (cx - r * 0.25, cy + r * 0.35),
            (cx, cy + r * 0.55),
            (cx + r * 0.25, cy + r * 0.35),
        ]
        
        # Draw the bones
        pygame.draw.polygon(pelvis_surf, self.color, points_left)
        pygame.draw.polygon(pelvis_surf, outline_color, points_left, 2)
        pygame.draw.polygon(pelvis_surf, self.color, points_right)
        pygame.draw.polygon(pelvis_surf, outline_color, points_right, 2)
        pygame.draw.polygon(pelvis_surf, self.color, sacrum_points)
        pygame.draw.polygon(pelvis_surf, outline_color, sacrum_points, 2)
        pygame.draw.polygon(pelvis_surf, self.color, pubis_points)
        pygame.draw.polygon(pelvis_surf, outline_color, pubis_points, 2)
        
        # Add iliac crest details
        pygame.draw.line(pelvis_surf, BONE_HIGHLIGHT, 
                         (cx - r * 0.6, cy - r * 0.55),
                         (cx - r * 0.9, cy - r * 0.2), 2)
        pygame.draw.line(pelvis_surf, BONE_HIGHLIGHT,
                         (cx + r * 0.6, cy - r * 0.55),
                         (cx + r * 0.9, cy - r * 0.2), 2)
        
        # Draw glow effect if needed
        if glow:
            glow_surf = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
            for rad in range(12, 25, 3):
                alpha = int(80 * (1 - (rad - 12) / 13))
                pygame.draw.circle(glow_surf, (*MATCH_GOOD_COL, alpha), 
                                  (w // 2 + 10, h // 2 + 10), rad)
            pelvis_surf.blit(glow_surf, (-10, -10))
        
        # Rotate and blit
        rotated = pygame.transform.rotate(pelvis_surf, -self.angle)
        rect = rotated.get_rect(center=(self.x, self.y))
        surface.blit(rotated, rect)
        
        return rotated.get_rect()


class PelvisMinigame(BaseMinigame):
    """
    Pelvic bone alignment puzzle.
    Match the rotating pelvis with the fixed target orientation.
    3 successful matches required to succeed.
    """
    
    def __init__(self, screen, fonts, patient, region="pelvis"):
        super().__init__(screen, fonts, patient, region)
        self.W, self.H = screen.get_size()
        
        severity = patient.get("severity", 5)
        # Slower rotation: 60-90 degrees per second (was 120-195)
        self._rotation_speed = 50 + (severity - 1) * 8  # 50-82 degrees per second
        self._tolerance = 18  # degrees of tolerance for a match (was 12, now larger)
        self._matches_needed = 3
        self._matches_made = 0
        self._attempts = 0
        self._max_attempts = 5
        
        # Pelvis positions
        self._target_y = int(self.H * 0.32)
        self._rotating_y = int(self.H * 0.68)
        self._pelvis_size = 110
        
        # Create pelvis objects
        self._target_pelvis = Pelvis(self.W // 2, self._target_y, self._pelvis_size)
        self._rotating_pelvis = Pelvis(self.W // 2, self._rotating_y, self._pelvis_size)
        
        # Set random target angle
        self._target_angle = random.randint(0, 359)
        self._target_pelvis.set_angle(self._target_angle)
        
        # Start rotating pelvis at random angle
        self._rotating_pelvis.set_angle(random.randint(0, 359))
        
        # Game state
        self.game_result = None
        self._current_attempt_active = True
        self._match_flash_timer = 0
        self._match_flash_color = None
        self._shake_timer = 0
        self._match_message = ""
        self._match_message_timer = 0
        
        # Animation states for result screen
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
        self._cutscene_printed = False  # To prevent console spam
        
        # Fade in
        self._game_fade_alpha = 255
        self._fade_surf = pygame.Surface((self.W, self.H))
        self._fade_surf.fill((0, 0, 0))
        
    def _check_alignment(self):
        """Check if rotating pelvis matches target angle"""
        diff = abs(self._rotating_pelvis.angle - self._target_angle)
        diff = min(diff, 360 - diff)
        
        if diff <= self._tolerance:
            # Perfect match (within 8 degrees)
            if diff <= 8:
                self._match_flash_color = PERFECT_COL
                self._match_message = "PERFECT ALIGNMENT!"
                self._matches_made += 1
            # Good match
            else:
                self._match_flash_color = GOOD_COL
                self._match_message = "GOOD ALIGNMENT!"
                self._matches_made += 1
            
            self._match_flash_timer = 0.6
            self._match_message_timer = 0.8
            self._current_attempt_active = True
            
            # Check if all matches completed
            if self._matches_made >= self._matches_needed:
                self.game_result = True
                print(f"[PelvisMinigame] ALL {self._matches_needed} MATCHES COMPLETE! Result = True")
            
            # After a match, set a new random target angle
            self._target_angle = random.randint(0, 359)
            self._target_pelvis.set_angle(self._target_angle)
            
        else:
            # Miss - too far off
            self._match_flash_color = MISS_COL
            self._match_message = f"MISALIGNED! ({int(diff)}° off)"
            self._match_flash_timer = 0.6
            self._match_message_timer = 1.0
            self._shake_timer = 0.3
            self._attempts += 1
            self._current_attempt_active = True
            
            # Too many attempts = failure
            if self._attempts >= self._max_attempts:
                self.game_result = False
                print(f"[PelvisMinigame] TOO MANY ATTEMPTS! Result = False")
    
    def _attempt_match(self):
        """Player attempts to match the rotating pelvis with target"""
        if self.game_result is not None:
            return
        if not self._current_attempt_active:
            return
            
        self._check_alignment()
        self._current_attempt_active = False
        
        # Reset after a short delay
        if self.game_result is None:
            import threading
            def reset_attempt():
                pygame.time.wait(300)
                self._current_attempt_active = True
            threading.Thread(target=reset_attempt, daemon=True).start()
    
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
        self._cutscene_printed = False

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
                        elif self.anim_state == "return_text":
                            return self.game_result
                
                # Game input during gameplay
                if not self.anim_state and self.game_result is None:
                    triggered = (
                        (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or
                        (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
                    )
                    if triggered:
                        self._attempt_match()
            
            # Update game logic
            if self.game_result is None:
                self._update_game(dt)
            
            # Start result screen when game ends
            if self.game_result is not None and not self.anim_state:
                self.anim_state = "title"
                self._setup_title_animation()
                self.title_complete = False
                self.result_start_time = pygame.time.get_ticks()

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
            
            # Update return text animation
            if self.anim_state == "return_text" and self.return_anim:
                self.return_anim.update(dt)
                if self.return_anim.is_complete() and not self._cutscene_printed:
                    self._cutscene_printed = True
                    self.waiting_for_continue = True
                    self.continue_prompt_visible = True
                    self.auto_continue_timer = pygame.time.get_ticks()
            
            # Auto-continue timer for subtitle screen
            if self.anim_state == "subtitle" and self.waiting_for_continue:
                if pygame.time.get_ticks() - self.auto_continue_timer >= self.auto_continue_delay:
                    self.anim_state = "fade_out"
                    self.fade_target = 0
                    self.waiting_for_continue = False
                    self.continue_prompt_visible = False
            
            # Auto-continue timer for return text screen
            if self.anim_state == "return_text" and self.waiting_for_continue:
                if pygame.time.get_ticks() - self.auto_continue_timer >= self.auto_continue_delay:
                    return self.game_result

            self._draw()
            pygame.display.flip()

    def _update_game(self, dt):
        """Update game logic"""
        if self._game_fade_alpha > 0:
            self._game_fade_alpha = max(0, self._game_fade_alpha - 320 * dt)
        
        # Rotate the moving pelvis
        self._rotating_pelvis.rotate(self._rotation_speed * dt)
        
        # Update timers
        if self._match_flash_timer > 0:
            self._match_flash_timer -= dt
        if self._match_message_timer > 0:
            self._match_message_timer -= dt
        if self._shake_timer > 0:
            self._shake_timer = max(0, self._shake_timer - dt)

    def _draw(self):
        W, H = self.W, self.H
        
        # Screen shake offset
        shake = 0
        if self._shake_timer > 0:
            shake = int(math.sin(self._shake_timer * 60) * self._shake_timer * 14)
        
        self.screen.fill(BG_COL)
        self._draw_grid()
        
        # Draw game elements (only if not in result animation)
        if not self.anim_state:
            self._draw_ui()
            self._draw_instruction()
            self._draw_progress()
            
            # Draw target pelvis
            self._target_pelvis.draw(self.screen, OUTLINE_COL)
            
            # Draw rotating pelvis with glow if aligned
            glow = (self._match_flash_timer > 0 and self._match_flash_color == PERFECT_COL)
            self._rotating_pelvis.draw(self.screen, OUTLINE_COL, glow)
            
            # Draw alignment arc indicator
            self._draw_alignment_indicator()
            
            # Draw match result message
            if self._match_message_timer > 0 and self._match_message:
                alpha = int(255 * min(1.0, self._match_message_timer / 0.5))
                msg_surf = self.fonts['large'].render(self._match_message, True, self._match_flash_color)
                msg_surf.set_alpha(alpha)
                msg_rect = msg_surf.get_rect(center=(W // 2, self._rotating_y - 80))
                self.screen.blit(msg_surf, msg_rect)
        
        if self._game_fade_alpha > 0 and not self.anim_state:
            self._fade_surf.set_alpha(int(self._game_fade_alpha))
            self.screen.blit(self._fade_surf, (0, 0))
        
        # Draw result overlay
        if self.anim_state:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            
            if self.title_anim and self.anim_state in ["title", "subtitle", "fade_out"]:
                title_y = H // 2 - 100
                self.title_anim.draw(self.screen, W // 2, title_y, center_x=True)
            
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
            
            if self.anim_state == "return_text" and self.return_anim:
                self.return_anim.draw(self.screen, W // 2, H // 2, center_x=True)
            
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

    def _draw_grid(self):
        """Draw faint grid lines"""
        W, H = self.W, self.H
        for x in range(0, W, 50):
            pygame.draw.line(self.screen, GRID_COL, (x, 0), (x, H))
        for y in range(0, H, 50):
            pygame.draw.line(self.screen, GRID_COL, (0, y), (W, y))

    def _draw_alignment_indicator(self):
        """Draw an arc showing alignment difference"""
        W, H = self.W, self.H
        
        # Calculate angle difference
        diff = abs(self._rotating_pelvis.angle - self._target_angle)
        diff = min(diff, 360 - diff)
        
        # Draw arc circle between the two pelvises
        center_x = W // 2
        center_y = (self._target_y + self._rotating_y) // 2
        radius = 80
        
        # Background arc (full circle)
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            x = center_x + int(radius * math.cos(rad))
            y = center_y + int(radius * math.sin(rad))
            pygame.draw.circle(self.screen, (40, 50, 60), (x, y), 2)
        
        # Alignment indicator arc (shows how close you are)
        if diff <= 5:
            color = PERFECT_COL
        elif diff <= self._tolerance:
            color = GOOD_COL
        else:
            color = MISS_COL
        
        # Draw the indicator arc
        for angle in range(0, 360, 5):
            if abs(angle - self._rotating_pelvis.angle % 360) <= diff + 5:
                rad = math.radians(angle)
                x = center_x + int(radius * math.cos(rad))
                y = center_y + int(radius * math.sin(rad))
                pygame.draw.circle(self.screen, color, (x, y), 3)
        
        # Draw connecting lines
        pygame.draw.line(self.screen, (50, 60, 70), 
                        (W // 2, self._target_y + 40), 
                        (center_x, center_y - 20), 1)
        pygame.draw.line(self.screen, (50, 60, 70),
                        (W // 2, self._rotating_y - 40),
                        (center_x, center_y + 20), 1)

    def _draw_ui(self):
        """Draw UI elements"""
        W, H = self.W, self.H
        p = self.patient
        
        # Patient header
        self.screen.blit(self.fonts['large'].render(
            f"{p['name']}, {p['age']}", True, TEXT_COL), (36, 20))
        self.screen.blit(self.fonts['small'].render(
            p['condition'], True, MUTED_COL), (36, 48))
        
        # Region top-right - LARGER FONT
        reg = self.fonts['large'].render("OPERATING: PELVIS", True, ACCENT_COL)
        self.screen.blit(reg, (W - reg.get_width() - 36, 28))

    def _draw_progress(self):
        """Draw match progress and attempts"""
        W, H = self.W, self.H
        
        # Progress bar background
        bar_x = W // 2 - 150
        bar_y = H - 80
        bar_w = 300
        bar_h = 16
        
        pygame.draw.rect(self.screen, (30, 35, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=8)
        
        # Fill based on matches made
        if self._matches_needed > 0:
            fill_w = int(bar_w * (self._matches_made / self._matches_needed))
            if fill_w > 0:
                color = PERFECT_COL if self._matches_made >= self._matches_needed else ACCENT_COL
                pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_w, bar_h), border_radius=8)
        
        pygame.draw.rect(self.screen, (80, 90, 100), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=8)
        
        # Text
        prog_text = self.fonts['medium'].render(
            f"ALIGNMENTS: {self._matches_made}/{self._matches_needed}", True, TEXT_COL)
        self.screen.blit(prog_text, ((W - prog_text.get_width()) // 2, bar_y - 28))
        
        # Attempt counter - MORE CLEAR, larger and highlighted
        attempts_left = self._max_attempts - self._attempts
        if attempts_left <= 1:
            attempt_color = MISS_COL
        elif attempts_left <= 2:
            attempt_color = GOOD_COL
        else:
            attempt_color = MUTED_COL
            
        attempts_text = self.fonts['large'].render(
            f"REMAINING ATTEMPTS: {attempts_left}", True, attempt_color)
        self.screen.blit(attempts_text, (36, H - 55))

    def _draw_instruction(self):
        """Draw instructions at top of screen"""
        W, H = self.W, self.H
        
        # Instruction at top
        inst_text = "Press SPACE or CLICK when the rotating pelvis matches the target"
        inst = self.fonts['medium'].render(inst_text, True, ACCENT_COL)
        inst_rect = inst.get_rect(center=(W // 2, 85))
        self.screen.blit(inst, inst_rect)
        
        # Angle difference display
        diff = abs(self._rotating_pelvis.angle - self._target_angle)
        diff = min(diff, 360 - diff)
        
        if diff <= self._tolerance:
            color = GOOD_COL
        else:
            color = MISS_COL
            
        angle_text = self.fonts['small'].render(f"ALIGNMENT: {int(diff)}° off", True, color)
        angle_rect = angle_text.get_rect(center=(W // 2, 120))
        self.screen.blit(angle_text, angle_rect)