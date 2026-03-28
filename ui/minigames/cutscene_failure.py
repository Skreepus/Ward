"""
Failure cutscene for surgery outcomes
"""
import pygame
import math

# Colors
FAIL_RED = (180, 40, 40)
TEXT_COL = (160, 160, 150)
MUTED_COL = (80, 80, 70)


class FailureCutscene:
    """Failure cutscene - shows when surgery fails"""
    
    def __init__(self, screen, fonts, patient_name: str):
        self.screen = screen
        self.fonts = fonts
        self.patient_name = patient_name
        
        # Cutscene content
        self.title = "SURGERY FAILED"
        self.subtitle = "Complications Occurred"
        self.lines = [
            f"The surgery on {patient_name} encountered complications.",
            "Despite best efforts, the patient could not be stabilized.",
            "The surgical team is reviewing the procedure.",
            "",
            "The family has been informed.",
            "This outcome will be reviewed by the board."
        ]
        self.color = FAIL_RED
        
        # Animation timing
        self.duration = 3.5  # seconds total
        self.elapsed = 0.0
        self.alpha = 0
        self.fade_in_duration = 0.5
        self.fade_out_duration = 0.5
        self.waiting_for_key = False
        
    def update(self, dt):
        """Update cutscene animation. Returns True when cutscene is complete."""
        self.elapsed += dt
        
        # Calculate alpha based on fade in/out
        if self.elapsed < self.fade_in_duration:
            # Fade in
            self.alpha = int(255 * (self.elapsed / self.fade_in_duration))
            self.waiting_for_key = False
        elif self.elapsed > self.duration - self.fade_out_duration:
            # Fade out
            fade_out_progress = (self.elapsed - (self.duration - self.fade_out_duration)) / self.fade_out_duration
            self.alpha = int(255 * (1 - fade_out_progress))
            self.waiting_for_key = False
        elif self.elapsed < self.duration:
            # Full visibility, allow key press
            self.alpha = 255
            self.waiting_for_key = True
        else:
            self.alpha = 0
            self.waiting_for_key = False
            return True
        
        return False
    
    def draw(self):
        """Draw the cutscene overlay"""
        W, H = self.screen.get_size()
        
        # Draw dark overlay
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        overlay.set_alpha(min(255, self.alpha))
        self.screen.blit(overlay, (0, 0))
        
        # Draw title
        title_surf = self.fonts['xlarge'].render(self.title, True, self.color)
        title_rect = title_surf.get_rect(center=(W // 2, H // 3))
        title_surf.set_alpha(self.alpha)
        self.screen.blit(title_surf, title_rect)
        
        # Draw subtitle
        sub_surf = self.fonts['large'].render(self.subtitle, True, TEXT_COL)
        sub_rect = sub_surf.get_rect(center=(W // 2, H // 3 + 55))
        sub_surf.set_alpha(self.alpha)
        self.screen.blit(sub_surf, sub_rect)
        
        # Draw text lines
        y_offset = H // 3 + 110
        for line in self.lines:
            if line == "":
                y_offset += 15
                continue
            line_surf = self.fonts['medium'].render(line, True, TEXT_COL)
            line_rect = line_surf.get_rect(center=(W // 2, y_offset))
            line_surf.set_alpha(self.alpha)
            self.screen.blit(line_surf, line_rect)
            y_offset += 32
        
        # Draw continue hint when waiting
        if self.waiting_for_key and self.alpha > 200:
            hint = self.fonts['small'].render("Press any key to continue...", True, MUTED_COL)
            hint_rect = hint.get_rect(center=(W // 2, H - 50))
            pulse = abs(math.sin(pygame.time.get_ticks() / 500))
            hint.set_alpha(int(150 + 105 * pulse))
            self.screen.blit(hint, hint_rect)