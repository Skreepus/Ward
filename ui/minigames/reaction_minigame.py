"""
Generic reaction minigame - press SPACE in the green zone.
"""
import pygame
import sys
from .base import BaseMinigame

BG_DARK = (8, 12, 10)
TEXT_COL = (160, 160, 150)
MUTED_COL = (80, 80, 70)
DIM = (0, 0, 0, 160)


class ReactionMinigame(BaseMinigame):
    """
    Generic fallback minigame for body regions not yet assigned.
    A bar fills left-to-right; press SPACE in the green zone to succeed.
    """

    FILL_SPEED = 0.45
    ZONE_START = 0.42
    ZONE_END = 0.72

    def __init__(self, screen, fonts, patient, region=None):
        super().__init__(screen, fonts, patient, region)
        self.W, self.H = screen.get_size()
        self.progress = 0.0
        self._fade_alpha = 255
        self._fade = pygame.Surface((self.W, self.H))
        self._fade.fill((0, 0, 0))

    def run(self) -> bool:
        clock = pygame.time.Clock()
        while self.result is None:
            dt = clock.tick(60) / 1000.0
            self._update(dt)
            self._handle_events()
            self._draw()
            pygame.display.flip()
        self._show_result()
        return self.result

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if self.ZONE_START <= self.progress <= self.ZONE_END:
                    self.result = True
                else:
                    self.result = False

    def _update(self, dt):
        if self._fade_alpha > 0:
            self._fade_alpha = max(0, self._fade_alpha - 300 * dt)
        self.progress = min(1.0, self.progress + self.FILL_SPEED * dt)
        if self.progress >= 1.0 and self.result is None:
            self.result = False

    def _draw(self):
        W, H = self.W, self.H
        self.screen.fill(BG_DARK)

        # Header
        p = self.patient
        self.screen.blit(self.fonts['large'].render(
            f"{p['name']}, {p['age']}", True, TEXT_COL), (36, 28))
        self.screen.blit(self.fonts['small'].render(
            p['condition'], True, MUTED_COL), (36, 54))

        if self.region:
            reg_s = self.fonts['small'].render(
                f"OPERATING: {self.region.upper()}", True, (148, 148, 72))
            self.screen.blit(reg_s, (W - reg_s.get_width() - 36, 28))

        # Bar
        bx, by = 200, H // 2 - 16
        bw, bh = W - 400, 32
        zone_x = bx + int(self.ZONE_START * bw)
        zone_w = int((self.ZONE_END - self.ZONE_START) * bw)

        pygame.draw.rect(self.screen, (25, 30, 25), (bx, by, bw, bh), border_radius=4)
        pygame.draw.rect(self.screen, (30, 80, 35), (zone_x, by, zone_w, bh), border_radius=4)

        fill_w = int(self.progress * bw)
        if self.progress < self.ZONE_START:
            fill_col = (148, 148, 72)
        elif self.progress > self.ZONE_END:
            fill_col = (175, 38, 38)
        else:
            fill_col = (60, 200, 80)

        pygame.draw.rect(self.screen, fill_col, (bx, by, fill_w, bh), border_radius=4)
        pygame.draw.rect(self.screen, (60, 70, 60), (bx, by, bw, bh), 1, border_radius=4)

        # Labels
        inst = self.fonts['medium'].render("Press SPACE in the green zone.", True, TEXT_COL)
        self.screen.blit(inst, ((W - inst.get_width()) // 2, H // 2 + 36))

        steady = self.fonts['small'].render("STEADY", True, MUTED_COL)
        self.screen.blit(steady, ((W - steady.get_width()) // 2, H // 2 - 56))

        if self._fade_alpha > 0:
            self._fade.set_alpha(int(self._fade_alpha))
            self.screen.blit(self._fade, (0, 0))

    def _show_result(self):
        W, H = self.W, self.H
        text = "STABLE" if self.result else "COMPLICATIONS"
        colour = (60, 200, 80) if self.result else (180, 40, 40)
        end = pygame.time.get_ticks() + 1800
        clock = pygame.time.Clock()
        while pygame.time.get_ticks() < end:
            clock.tick(60)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                # Any keypress skips the result screen (after 300ms grace period)
                if e.type == pygame.KEYDOWN:
                    if pygame.time.get_ticks() > end - 1500:
                        return
            self.screen.fill(BG_DARK)
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill(DIM)
            self.screen.blit(ov, (0, 0))
            s = self.fonts['xlarge'].render(text, True, colour)
            self.screen.blit(s, ((W - s.get_width()) // 2,
                                  H // 2 - s.get_height() // 2))
            hint = self.fonts['small'].render("Press any key to continue", True, (70, 70, 65))
            self.screen.blit(hint, ((W - hint.get_width()) // 2, H // 2 + 50))
            pygame.display.flip()