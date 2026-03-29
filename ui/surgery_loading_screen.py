import pygame
import sys
import os
import random

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Colours (match existing theme)
BG_COL   = (6, 6, 6)
TEXT_COL = (190, 188, 150)
DIM_COL  = (90, 88, 70)

class SurgeryLoadingScreen:
    """
    Brief, instant‑appearing transitional screen before surgery.
    Shows a technical message for a very short duration.
    """

    DEFAULT_MESSAGES = [
        "Preparing operating theatre.",
        "Scrubbing in.",
        "Transferring patient to surgery suite.",
        "Reviewing case notes.",
        "Calibrating instruments.",
        "Confirming anaesthesia protocol.",
    ]

    def __init__(self, screen, fonts, patient_name=None, duration=0.3):
        """
        screen: pygame display surface
        fonts: dict with keys 'medium', 'small'
        patient_name: optional, appended to message
        duration: seconds to show (default 0.3 for instant feel)
        """
        self.screen = screen
        self.fonts = fonts
        self.duration = duration
        self.W, self.H = screen.get_size()

        # Random message
        base_msg = random.choice(self.DEFAULT_MESSAGES)
        if patient_name:
            self.message = f"{base_msg} — {patient_name}"
        else:
            self.message = base_msg

        # Safe font loading
        self.medium_font = fonts.get('medium')
        if self.medium_font is None:
            self.medium_font = pygame.font.SysFont('monospace', 20)

        self.small_font = fonts.get('small')
        if self.small_font is None:
            self.small_font = pygame.font.SysFont('monospace', 14)

        # Pre‑render text
        self.text_surf = self.medium_font.render(self.message, True, TEXT_COL)

        # No fade – start fully visible
        self.alpha = 255
        self.timer = 0.0
        self.state = "hold"   # hold then exit (no fade out for speed)

    def run(self):
        """Show the screen instantly, hold for duration, then return."""
        clock = pygame.time.Clock()
        start_ticks = pygame.time.get_ticks()

        while True:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                # Allow SPACE to skip immediately
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    return

            # Timer
            if self.state == "hold":
                self.timer += dt
                if self.timer >= self.duration:
                    return

            # Draw – solid background, no fade
            self.screen.fill(BG_COL)

            # Center message
            x = (self.W - self.text_surf.get_width()) // 2
            y = (self.H - self.text_surf.get_height()) // 2
            self.screen.blit(self.text_surf, (x, y))

            # Small animated dots (only during hold)
            if self.state == "hold":
                dots = "." * ((pygame.time.get_ticks() // 200) % 4)
                loading_text = f"Loading{dots}"
                loading_surf = self.small_font.render(loading_text, True, DIM_COL)
                lx = (self.W - loading_surf.get_width()) // 2
                ly = y + self.text_surf.get_height() + 30
                self.screen.blit(loading_surf, (lx, ly))

            pygame.display.flip()