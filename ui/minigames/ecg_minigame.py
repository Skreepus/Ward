"""
ECG rhythm minigame for heart/chest conditions.
Player must intervene during 3 arrhythmia windows to stabilize the patient.
"""
import pygame
import math
import random
import sys
from .base import BaseMinigame

# Colors
BG_DARK   = (8, 12, 10)
GRID_COL  = (15, 28, 18)
ECG_GREEN = (60, 220, 100)
ECG_RED   = (180, 30, 30)
TEXT_COL  = (160, 160, 150)
MUTED_COL = (80, 80, 70)


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


class ECGMinigame(BaseMinigame):
    """
    ECG rhythm minigame for heart conditions.
    Player must intervene during 3 arrhythmia windows to stabilize the patient.
    Fast-paced version: 10 seconds total, 1.2 second windows.
    """

    SCROLL_SPEED = 380  # Faster scroll
    HISTORY_LEN = 900
    WINDOW_DURATION = 1.2  # 1.2 seconds to react
    ECG_AMP = 38
    
    # 3 intervention windows - tightly spaced
    WINDOW_1_START = 1.8
    WINDOW_2_START = 4.2
    WINDOW_3_START = 6.8
    
    TOTAL_TIME = 10.0  # 10 seconds total

    def __init__(self, screen, fonts, patient, region=None):
        super().__init__(screen, fonts, patient, region)
        self.W, self.H = screen.get_size()
        
        print(f"[ECGMinigame] Initializing for patient: {patient['name']}")

        severity = patient.get("severity", 5)
        self.instability = 0.5 + severity * 0.08  # More unstable rhythm

        self.ECG_Y = self.H // 2
        self._ecg_points = []
        self._scroll_acc = 0.0
        self.time_elapsed = 0.0
        
        # Window tracking
        self.windows = [
            {"start": self.WINDOW_1_START, "active": False, "hit": False},
            {"start": self.WINDOW_2_START, "active": False, "hit": False},
            {"start": self.WINDOW_3_START, "active": False, "hit": False},
        ]
        self.current_window_index = 0
        self.interventions_made = 0
        self.interventions_needed = 3
        
        self._beat_phase = 0.0
        self._beat_period = 0.55  # Faster heartbeat (~109 BPM)
        
        self.game_result = None
        
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

        self._prefill()

        self._game_fade_alpha = 255
        self._fade_surf = pygame.Surface((self.W, self.H))
        self._fade_surf.fill((0, 0, 0))
        
        print(f"[ECGMinigame] Initialized. Need {self.interventions_needed} interventions")
        print(f"[ECGMinigame] Windows at: {self.WINDOW_1_START}s, {self.WINDOW_2_START}s, {self.WINDOW_3_START}s")
        print(f"[ECGMinigame] Total time: {self.TOTAL_TIME}s, Window duration: {self.WINDOW_DURATION}s")

    def _prefill(self):
        phase = 0.0
        for _ in range(self.HISTORY_LEN):
            phase += 1.0 / (self.SCROLL_SPEED * self._beat_period / self.W)
            self._ecg_points.append(self._ecg_sample(phase, False))

    def _ecg_sample(self, phase: float, unstable: bool) -> float:
        t = phase % 1.0
        if not unstable:
            if t < 0.10:
                return math.sin(t / 0.10 * math.pi) * 8
            elif t < 0.45:
                return 0
            elif t < 0.48:
                return -math.sin((t - 0.45) / 0.03 * math.pi) * 12
            elif t < 0.52:
                return math.sin((t - 0.48) / 0.04 * math.pi) * self.ECG_AMP
            elif t < 0.56:
                return -math.sin((t - 0.52) / 0.04 * math.pi) * 10
            elif t < 0.75:
                return math.sin((t - 0.56) / 0.19 * math.pi) * 14
            else:
                return 0
        else:
            base = self._ecg_sample(phase, False)
            noise = random.gauss(0, self.instability * 20)  # More intense noise
            if random.random() < 0.05 * self.instability:  # More frequent spikes
                noise += random.choice([-1, 1]) * random.uniform(30, 70)
            return base + noise

    def run(self) -> bool:
        print(f"[ECGMinigame] Starting run()")
        clock = pygame.time.Clock()
        self.anim_state = None
        self.waiting_for_continue = False
        self.auto_continue_timer = 0
        self.title_complete = False

        while True:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Handle continue key press
                if self.waiting_for_continue:
                    if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.anim_state == "subtitle":
                            self.anim_state = "fade_out"
                            self.fade_target = 0
                            self.waiting_for_continue = False
                            self.continue_prompt_visible = False
                            print(f"[ECGMinigame] Continue pressed. Fading to black.")
                        elif self.anim_state == "return_text":
                            print(f"[ECGMinigame] Final continue pressed. Returning result: {self.game_result}")
                            return self.game_result
                
                # Game input during gameplay
                if not self.anim_state and self.game_result is None:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        self._handle_intervention()

            # Game logic
            if self.game_result is None:
                self._update_game(dt)
            
            # Start result screen when game ends
            if self.game_result is not None and not self.anim_state:
                self.anim_state = "title"
                self._setup_title_animation()
                self.title_complete = False
                print(f"[ECGMinigame] Result={self.game_result}. Starting title animation.")

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
                    print(f"[ECGMinigame] Title complete. Showing subtitle.")
            
            # Update return text animation
            if self.anim_state == "return_text" and self.return_anim:
                self.return_anim.update(dt)
                if self.return_anim.is_complete():
                    self.waiting_for_continue = True
                    self.continue_prompt_visible = True
                    self.auto_continue_timer = pygame.time.get_ticks()
                    print(f"[ECGMinigame] Return text complete. Waiting for continue.")
            
            # Auto-continue timer for subtitle screen
            if self.anim_state == "subtitle" and self.waiting_for_continue:
                if pygame.time.get_ticks() - self.auto_continue_timer >= self.auto_continue_delay:
                    self.anim_state = "fade_out"
                    self.fade_target = 0
                    self.waiting_for_continue = False
                    self.continue_prompt_visible = False
                    print(f"[ECGMinigame] Auto-advance after 20 seconds. Fading to black.")
            
            # Auto-continue timer for return text screen
            if self.anim_state == "return_text" and self.waiting_for_continue:
                if pygame.time.get_ticks() - self.auto_continue_timer >= self.auto_continue_delay:
                    print(f"[ECGMinigame] Auto-advance after 20 seconds. Returning result: {self.game_result}")
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
            speed=22
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
            speed=24
        )
        self.fade_target = 255

    def _handle_intervention(self):
        """Handle space bar intervention during active windows"""
        for i, window in enumerate(self.windows):
            if window["active"] and not window["hit"]:
                window["hit"] = True
                window["active"] = False
                self.interventions_made += 1
                
                print(f"[ECGMinigame] Intervention {self.interventions_made}/{self.interventions_needed} successful at {self.time_elapsed:.1f}s")
                
                if self.interventions_made >= self.interventions_needed:
                    self.game_result = True
                    print(f"[ECGMinigame] ALL 3 INTERVENTIONS COMPLETE! Result = True")
                break

    def _update_game(self, dt):
        """Update game logic"""
        if self._game_fade_alpha > 0:
            self._game_fade_alpha = max(0, self._game_fade_alpha - 380 * dt)

        self.time_elapsed += dt
        
        if int(self.time_elapsed) % 1 == 0 and int(self.time_elapsed) != int(self.time_elapsed - dt):
            print(f"[ECGMinigame] Time: {self.time_elapsed:.1f}s, Interventions: {self.interventions_made}/{self.interventions_needed}")
        
        self._beat_phase += dt / self._beat_period

        # Update window states
        for i, window in enumerate(self.windows):
            if not window["hit"] and not window["active"]:
                if self.time_elapsed >= window["start"]:
                    window["active"] = True
                    self.current_window_index = i
                    print(f"[ECGMinigame] Window {i+1} OPEN at {self.time_elapsed:.1f}s")
            
            if window["active"] and not window["hit"]:
                if self.time_elapsed >= window["start"] + self.WINDOW_DURATION:
                    window["active"] = False
                    print(f"[ECGMinigame] Window {i+1} CLOSED (missed) at {self.time_elapsed:.1f}s")
                    if self.interventions_made < self.interventions_needed:
                        self.game_result = False
                        print(f"[ECGMinigame] WINDOW MISSED! Result = False")
                        return

        # Generate ECG samples
        self._scroll_acc += self.SCROLL_SPEED * dt
        n = int(self._scroll_acc)
        self._scroll_acc -= n
        
        is_window_active = any(w["active"] and not w["hit"] for w in self.windows)
        
        for _ in range(n):
            self._ecg_points.append(
                self._ecg_sample(self._beat_phase, is_window_active))

        if len(self._ecg_points) > self.HISTORY_LEN:
            self._ecg_points = self._ecg_points[-self.HISTORY_LEN:]

        if self.time_elapsed >= self.TOTAL_TIME and self.game_result is None:
            self.game_result = False
            print(f"[ECGMinigame] TIMEOUT! Result = False")

    def _draw(self):
        """Draw the game screen"""
        W, H = self.W, self.H
        
        self.screen.fill(BG_DARK)

        # Grid
        for x in range(0, W, 40):
            pygame.draw.line(self.screen, GRID_COL, (x, 0), (x, H))
        for y in range(0, H, 40):
            pygame.draw.line(self.screen, GRID_COL, (0, y), (W, y))

        # Game elements (only show if not in result screen)
        if not self.anim_state:
            p = self.patient
            self.screen.blit(self.fonts['large'].render(
                f"{p['name']}, {p['age']}", True, TEXT_COL), (36, 28))
            self.screen.blit(self.fonts['small'].render(
                p['condition'], True, MUTED_COL), (36, 54))
            mon = self.fonts['small'].render("CARDIAC MONITOR", True, MUTED_COL)
            self.screen.blit(mon, (W - mon.get_width() - 36, 28))

            pts = self._ecg_points
            if len(pts) >= 2:
                coords = [(W - (len(pts) - i), int(self.ECG_Y - v))
                          for i, v in enumerate(pts)]
                is_window_active = any(w["active"] and not w["hit"] for w in self.windows)
                col = ECG_RED if is_window_active else ECG_GREEN
                pygame.draw.lines(self.screen, col, False, coords, 2)
                pygame.draw.circle(self.screen, col, coords[-1], 3)

            self._draw_progress()
            
            if self.game_result is None:
                is_window_active = any(w["active"] and not w["hit"] for w in self.windows)
                if is_window_active:
                    inst = self.fonts['medium'].render("INTERVENE — SPACE", True, (220, 60, 60))
                elif self.interventions_made < self.interventions_needed:
                    inst = self.fonts['small'].render("INTERVENE DURING ARRHYTHMIA", True, MUTED_COL)
                else:
                    inst = self.fonts['medium'].render("PATIENT STABILIZING...", True, (60, 200, 80))
                self.screen.blit(inst, ((W - inst.get_width()) // 2, H - 44))

            self._draw_timeline()
            
            if self.game_result is None:
                t_left = max(0, self.TOTAL_TIME - self.time_elapsed)
                is_window_active = any(w["active"] and not w["hit"] for w in self.windows)
                col = (180, 40, 40) if is_window_active else MUTED_COL
                t_s = self.fonts['medium'].render(f"{t_left:.1f}s", True, col)
                self.screen.blit(t_s, (W - t_s.get_width() - 36, 54))

            if self._game_fade_alpha > 0:
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
        
        if self.anim_state == "fade_out" and self.fade_alpha < 255:
            fade_overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            fade_overlay.fill((0, 0, 0, int(255 - self.fade_alpha)))
            self.screen.blit(fade_overlay, (0, 0))
            
            if self.fade_alpha == 0:
                self.anim_state = "return_text"
                self._setup_return_text()
                print(f"[ECGMinigame] Fade complete. Starting return text.")

    def _draw_progress(self):
        """Draw progress bar for interventions"""
        W, H = self.W, self.H
        bar_x = 36
        bar_y = 90
        bar_w = W - 72
        bar_h = 12
        
        pygame.draw.rect(self.screen, (30, 30, 28), (bar_x, bar_y, bar_w, bar_h))
        
        if self.interventions_needed > 0:
            fill_w = int(bar_w * (self.interventions_made / self.interventions_needed))
            if fill_w > 0:
                color = (60, 200, 80) if self.interventions_made >= self.interventions_needed else ECG_GREEN
                pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_w, bar_h))
        
        for i in range(1, self.interventions_needed):
            marker_x = bar_x + int(bar_w * (i / self.interventions_needed))
            pygame.draw.line(self.screen, (80, 80, 80), (marker_x, bar_y - 3), (marker_x, bar_y + bar_h + 3), 2)
        
        prog_text = self.fonts['small'].render(f"INTERVENTIONS: {self.interventions_made}/{self.interventions_needed}", True, MUTED_COL)
        self.screen.blit(prog_text, (bar_x, bar_y - 18))

    def _draw_timeline(self):
        """Draw timeline bar with window markers"""
        W = self.W
        bar_y = self.H - 24
        bar_h = 6
        
        pygame.draw.rect(self.screen, (30, 30, 28), (36, bar_y, W - 72, bar_h))
        
        for window in self.windows:
            wx = 36 + int((window["start"] / self.TOTAL_TIME) * (W - 72))
            ww = int((self.WINDOW_DURATION / self.TOTAL_TIME) * (W - 72))
            
            if window["hit"]:
                col = (60, 200, 80)
            elif self.time_elapsed > window["start"] + self.WINDOW_DURATION:
                col = (180, 40, 40)
            else:
                col = (148, 148, 72)
            
            pygame.draw.rect(self.screen, col, (wx, bar_y, ww, bar_h))
        
        cx = 36 + int((min(self.time_elapsed, self.TOTAL_TIME) / self.TOTAL_TIME) * (W - 72))
        pygame.draw.rect(self.screen, TEXT_COL, (cx - 1, bar_y - 3, 2, bar_h + 6))