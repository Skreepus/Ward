import pygame
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


# ── Colours ───────────────────────────────────────────────────────────────
BG_COL       = (0,   0,   0,  210)
TEXT_COL     = (190, 188, 150)
DIM_COL      = (80,  78,  62)
NAME_COL     = (100, 98,  78)
ACCENT_LINE  = (70,  68,  50)


STRIP_H     = 140
SLIDE_SPEED = 180    # slower — more deliberate


class FamilyOverlay:
    """
    A family member appears at the bottom of the screen.
    They say one thing. The game keeps running behind it.

    Non-blocking — call update() and draw() each frame.
    Check .done to know when finished.
    """

    DISPLAY_TIME = 7.0
    FADE_IN_TIME = 0.6
    FADE_OUT_TIME = 1.2

    def __init__(self, screen, fonts, patient: dict, line: str):
        self.screen  = screen
        self.fonts   = fonts
        self.patient = patient
        self.line    = line

        W, H         = screen.get_size()
        self.W       = W
        self.H       = H

        self._strip_y    = float(H)
        self._target_y   = float(H - STRIP_H)
        self._hold_timer = 0.0
        self._fading     = False
        self._alpha      = 0.0        # fades in AND out
        self.done        = False

        self._relation   = self._infer_relation(patient)
        self._arrived    = False      # True once strip reaches target

    def _infer_relation(self, patient: dict) -> str:
        age = patient.get("age", 40)
        if age < 18:
            return "A parent has been waiting outside."
        elif age < 30:
            return "Someone is at the desk. They have been there a while."
        elif age < 50:
            return "A family member came in. They do not know what to do with their hands."
        elif age < 65:
            return "Someone drove here. They are still in their coat."
        else:
            return "Someone has been sitting in the waiting area since this morning."

    def update(self, dt: float):
        if self.done:
            return

        # Slide in
        if self._strip_y > self._target_y:
            self._strip_y = max(self._target_y, self._strip_y - SLIDE_SPEED * dt)

        # Fade in once arrived
        if self._strip_y <= self._target_y + 1:
            self._arrived = True

        if self._arrived and not self._fading:
            self._alpha = min(255, self._alpha + (255 / self.FADE_IN_TIME) * dt)

        # Hold
        if self._alpha >= 255 and not self._fading:
            self._hold_timer += dt
            if self._hold_timer >= self.DISPLAY_TIME:
                self._fading = True

        # Fade out
        if self._fading:
            self._alpha = max(0, self._alpha - (255 / self.FADE_OUT_TIME) * dt)
            if self._alpha <= 0:
                self.done = True

    def dismiss(self):
        self._fading = True

    def draw(self):
        if self.done:
            return

        W     = self.W
        y     = int(self._strip_y)
        alpha = int(self._alpha)

        # Build strip surface
        surf = pygame.Surface((W, STRIP_H), pygame.SRCALPHA)

        # Background — dark, slightly warm
        pygame.draw.rect(surf, (10, 9, 7, 220), (0, 0, W, STRIP_H))

        # Top border
        pygame.draw.line(surf, (55, 53, 40), (0, 0), (W, 0), 1)

        # Left accent bar
        pygame.draw.rect(surf, (75, 72, 52), (0, 0, 2, STRIP_H))

        # Relation label — dim, small, top
        rel_surf = self.fonts['small'].render(self._relation, True, DIM_COL)
        surf.blit(rel_surf, (28, 18))

        # The line — larger, more room to breathe
        quote = f'"{self.line}"'
        line_surf = self.fonts['medium'].render(quote, True, TEXT_COL)
        surf.blit(line_surf, (28, 44))

        # Thin rule
        pygame.draw.line(surf, ACCENT_LINE, (28, 86), (W - 28, 86), 1)

        # Patient name and condition — dim, bottom
        name    = self.patient.get('name', '')
        cond    = self.patient.get('condition', '')
        subline = f"{name}  —  {cond}"
        sub_surf = self.fonts['small'].render(subline, True, NAME_COL)
        surf.blit(sub_surf, (28, 98))

        # Apply overall alpha
        surf.set_alpha(alpha)
        self.screen.blit(surf, (0, y))