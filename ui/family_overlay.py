import pygame
import sys
import os

# Optional: add project path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FamilyOverlay:
    """
    Full‑screen modal that shows a family member's message.
    Blocks all game input until dismissed (click or SPACE).
    Matches the dark, pixel‑art aesthetic of WARD.
    """

    def __init__(self, screen, fonts, patient: dict, line: str):
        """
        screen: pygame display surface
        fonts: dict with keys 'small', 'medium', 'large' (fallbacks provided)
        patient: dict containing 'name', 'age', 'condition', etc.
        line: the dialogue line from the family member
        """
        self.screen = screen
        self.fonts = fonts
        self.patient = patient
        self.line = line
        self.done = False

        self.W, self.H = screen.get_size()

        # Pre‑render all text surfaces (so we don't re‑render every frame)
        self._render_texts()

        # Animation state
        self.alpha = 0               # current opacity (0‑255)
        self.fade_speed = 500        # alpha per second
        self.state = "fade_in"       # fade_in → hold → fade_out

        # Optional auto‑dismiss (disabled by default – requires click/SPACE)
        self.auto_dismiss = False
        self.hold_time = 0.0

        print(f"[FamilyOverlay] Created for {patient.get('name', 'Unknown')}")

    def _get_font(self, key: str, default_size: int):
        """Return a font from self.fonts or a sensible fallback."""
        font = self.fonts.get(key)
        if font is None:
            # Fallback to system monospace
            return pygame.font.SysFont('monospace', default_size)
        return font

    def _render_texts(self):
        """Render all static text elements."""
        # Use fallback fonts if the provided ones are missing
        small_font = self._get_font('small', 16)
        medium_font = self._get_font('medium', 24)
        large_font = self._get_font('large', 32)   # not used here, but available

        # Colours (match the game's muted palette)
        TEXT_COL = (190, 188, 150)      # warm off‑white
        ACCENT_COL = (70, 68, 50)       # dark muted gold
        NAME_COL = (100, 98, 78)        # dimmer gold
        PROMPT_COL = (120, 118, 90)     # very dim for continue text

        # Relation line (e.g., "A family member came in...")
        relation = self._infer_relation(self.patient)
        self.relation_surf = small_font.render(relation, True, ACCENT_COL)

        # The quote (with quotes)
        quote_text = f'"{self.line}"'
        self.quote_surf = medium_font.render(quote_text, True, TEXT_COL)

        # Patient name and condition
        name = self.patient.get('name', 'Unknown')
        cond = self.patient.get('condition', '')
        subline = f"{name}  –  {cond}"
        self.sub_surf = small_font.render(subline, True, NAME_COL)

        # Continue prompt (only visible in "hold" state)
        self.continue_surf = small_font.render(
            "press SPACE to continue",
            True, PROMPT_COL
        )

    def _infer_relation(self, patient: dict) -> str:
        """Return a short description of the family member based on patient's age."""
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
        """Call this every frame with delta time in seconds."""
        if self.done:
            return

        if self.state == "fade_in":
            self.alpha += self.fade_speed * dt
            if self.alpha >= 255:
                self.alpha = 255
                self.state = "hold"
        elif self.state == "hold":
            if self.auto_dismiss:
                self.hold_time += dt
                if self.hold_time >= 5.0:   # auto‑dismiss after 5 seconds
                    self.state = "fade_out"
        elif self.state == "fade_out":
            self.alpha -= self.fade_speed * dt
            if self.alpha <= 0:
                self.alpha = 0
                self.done = True

    def handle_event(self, event):
        """
        Call this from your main event loop while the overlay is active.
        It will dismiss the overlay on mouse click or SPACE.
        """
        if self.done:
            return
        if self.state == "hold":
            if event.type == pygame.MOUSEBUTTONDOWN or \
               (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                self.state = "fade_out"

    def dismiss(self):
        """Dismiss the overlay immediately (forced dismissal)."""
        if not self.done:
            self.state = "fade_out"
            # Force fast fade out
            self.fade_speed = 800

    def draw(self):
        """Draw the full‑screen overlay (should be called last, after game drawing)."""
        if self.done:
            return

        # Create a semi‑transparent dark surface
        overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        # Black with opacity based on current alpha (0‑255)
        overlay.fill((0, 0, 0, int(self.alpha * 0.85)))

        # Calculate vertical centering for all text blocks
        total_height = (self.relation_surf.get_height() +
                        self.quote_surf.get_height() +
                        self.sub_surf.get_height() +
                        self.continue_surf.get_height() + 60)
        y = (self.H - total_height) // 2

        # 1. Relation line (small, above quote)
        x = (self.W - self.relation_surf.get_width()) // 2
        overlay.blit(self.relation_surf, (x, y))
        y += self.relation_surf.get_height() + 20

        # 2. Quote (larger)
        x = (self.W - self.quote_surf.get_width()) // 2
        overlay.blit(self.quote_surf, (x, y))
        y += self.quote_surf.get_height() + 30

        # 3. Patient name + condition
        x = (self.W - self.sub_surf.get_width()) // 2
        overlay.blit(self.sub_surf, (x, y))
        y += self.sub_surf.get_height() + 40

        # 4. Continue prompt
        x = (self.W - self.continue_surf.get_width()) // 2
        overlay.blit(self.continue_surf, (x, y))

        # Apply overall fade effect
        overlay.set_alpha(self.alpha)
        self.screen.blit(overlay, (0, 0))