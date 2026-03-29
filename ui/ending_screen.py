import pygame
import sys
from .config import W, H

class EndingScreen:
    def __init__(self, screen, fonts, ending_data):
        self.screen = screen
        self.fonts = fonts
        self.ending = ending_data
        self.done = False
        self.W, self.H = screen.get_size()

        # Safe font loading – fallback to default if missing
        self.title_font = self._safe_font(fonts, 'large', 36)
        self.sub_font   = self._safe_font(fonts, 'medium', 24)
        self.body_font  = self._safe_font(fonts, 'small', 18)
        self.continue_font = self._safe_font(fonts, 'small', 16)

        # Wrap body text
        self.body_lines = self._wrap_text(ending_data.get("body", ""), self.body_font, self.W - 100)

        # Context handling (safe)
        self.context = ending_data.get("context", {})
        self.context_lines = []
        if "quiet_patients" in self.context:
            self.context_lines.append("\nThese patients had no one:")
            for p in self.context["quiet_patients"]:
                self.context_lines.append(f"  – {p['name']} ({p['condition']})")
        if "dead_names" in self.context:
            self.context_lines.append("\nThose who died on your shift:")
            for name in self.context["dead_names"]:
                self.context_lines.append(f"  – {name}")
        if "died_waiting" in self.context and self.context["died_waiting"]:
            p = self.context["died_waiting"]
            self.context_lines.append(f"\n{p['name']} died waiting.\n{p['condition']}.")
        if "patient_list" in self.context:
            self.context_lines.append("\nAll patients seen:")
            for p in self.context["patient_list"]:
                self.context_lines.append(f"  – {p['name']} ({p['condition']})")

        # Wrap context lines
        wrapped = []
        for line in self.context_lines:
            if line.startswith("  ") or line.startswith("\n"):
                wrapped.append(line)
            else:
                wrapped.extend(self._wrap_text(line, self.body_font, self.W - 100))
        self.context_lines = wrapped

        print("[EndingScreen] Initialized successfully")

    def _safe_font(self, fonts, key, default_size):
        font = fonts.get(key)
        if font is None:
            print(f"[EndingScreen] Warning: font '{key}' not found, using SysFont")
            return pygame.font.SysFont("monospace", default_size)
        return font

    def _wrap_text(self, text, font, max_width):
        if not text:
            return []
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def run(self):
        clock = pygame.time.Clock()
        try:
            while not self.done:
                dt = clock.tick(60) / 1000.0
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return "quit"
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        self.done = True
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.done = True

                self.screen.fill((0, 0, 0))

                # Title
                title_surf = self.title_font.render(self.ending.get("title", "The End"), True, (200, 200, 150))
                self.screen.blit(title_surf, (self.W//2 - title_surf.get_width()//2, 60))

                # Subtitle
                subtitle = self.ending.get("subtitle", "")
                if subtitle:
                    sub_surf = self.sub_font.render(subtitle, True, (150, 150, 100))
                    self.screen.blit(sub_surf, (self.W//2 - sub_surf.get_width()//2, 110))

                # Body
                y = 170
                for line in self.body_lines:
                    line_surf = self.body_font.render(line, True, (180, 180, 140))
                    self.screen.blit(line_surf, (50, y))
                    y += line_surf.get_height() + 4

                # Context lines
                for line in self.context_lines:
                    if line.startswith("\n"):
                        y += 15
                        line = line[1:]
                    line_surf = self.body_font.render(line, True, (130, 130, 100))
                    self.screen.blit(line_surf, (70, y))
                    y += line_surf.get_height() + 2

                # Continue prompt
                cont_surf = self.continue_font.render("Press SPACE or click to continue", True, (100, 100, 80))
                self.screen.blit(cont_surf, (self.W//2 - cont_surf.get_width()//2, self.H - 50))

                pygame.display.flip()

        except Exception as e:
            print(f"[EndingScreen] CRASH: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: wait for key press then exit
            self.screen.fill((0,0,0))
            err_surf = self.body_font.render("Error displaying ending. Press any key.", True, (255,0,0))
            self.screen.blit(err_surf, (self.W//2 - err_surf.get_width()//2, self.H//2))
            pygame.display.flip()
            while True:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT or e.type == pygame.KEYDOWN:
                        return "quit"
        return "menu"