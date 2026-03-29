import pygame
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Colours
BG_COL    = (6, 6, 6)
TEXT_COL  = (190, 188, 150)
DIM_COL   = (90, 88, 70)
LINE_COL  = (35, 35, 30)
DOT_COL   = (120, 118, 90)

# Story lines — shown one at a time, typewriter style
BRIEFING = [
    ("", 0.0),
    ("03:47.", 1.2),
    ("You are already here.", 1.8),
    ("", 0.6),
    ("The previous doctor went home four hours ago.", 2.0),
    ("You were called in.", 1.8),
    ("You did not ask why.", 1.4),
    ("", 0.6),
    ("One window. One Theatre", 1.8),
    ("One surgeon on call.", 2.2),
    ("", 0.6),
    ("", 0.5),
    ("Time to clock in", 2.8),
]

class LoadingScreen:
    """
    Displays the briefing text one line at a time while the first round
    loads in the background.
    """

    CPS       = 28      # characters per second for typewriter
    LINE_GAP  = 34      # px between lines
    START_Y   = 180     # y of first line

    def __init__(self, screen, fonts):
        self.screen = screen
        self.fonts  = fonts
        W, H        = screen.get_size()
        self.W      = W
        self.H      = H

        # Fade surfaces
        self._fade_in        = pygame.Surface((W, H))
        self._fade_in.fill(BG_COL)
        self._fade_alpha     = 255

        self._fade_out       = pygame.Surface((W, H))
        self._fade_out.fill(BG_COL)
        self._fade_out_alpha = 0

    def run(self, loader=None):
        """
        Runs the loading screen.
        loader: optional RoundLoader — waits for it before fading out.
        """
        clock         = pygame.time.Clock()
        line_index    = 0
        char_progress = 0.0
        line_hold     = 0.0
        shown_lines   = []
        text_done     = False
        fading_out    = False

        while True:
            dt = clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and text_done:
                        fading_out = True

            # Fade in
            if self._fade_alpha > 0:
                self._fade_alpha = max(0, self._fade_alpha - 220 * dt)

            # Typewriter progress
            if not text_done and self._fade_alpha == 0:
                if line_index < len(BRIEFING):
                    text, hold_time = BRIEFING[line_index]

                    if text == "":
                        line_hold += dt
                        if line_hold >= hold_time:
                            line_hold = 0.0
                            shown_lines.append(("", "gap"))
                            line_index += 1
                    else:
                        char_progress += self.CPS * dt
                        chars_shown = int(char_progress)

                        if chars_shown >= len(text):
                            line_hold += dt
                            if line_hold >= hold_time:
                                line_hold = 0.0
                                char_progress = 0.0
                                shown_lines.append((text, "done"))
                                line_index += 1
                else:
                    text_done = True

            # Auto fade out once text done and loader ready
            if text_done:
                loader_ready = (loader is None) or loader.is_ready()
                if loader_ready:
                    fading_out = True

            if fading_out:
                self._fade_out_alpha = min(255, self._fade_out_alpha + 180 * dt)
                if self._fade_out_alpha >= 255:
                    return

            # Draw
            self.screen.fill(BG_COL)
            self._draw_lines(shown_lines, line_index, char_progress)
            self._draw_footer(text_done, loader)

            # Fade in overlay
            if self._fade_alpha > 0:
                self._fade_in.set_alpha(int(self._fade_alpha))
                self.screen.blit(self._fade_in, (0, 0))

            # Fade out overlay
            if fading_out and self._fade_out_alpha > 0:
                self._fade_out.set_alpha(int(self._fade_out_alpha))
                self.screen.blit(self._fade_out, (0, 0))

            pygame.display.flip()

    def _draw_lines(self, shown_lines, current_index, char_progress):
        W  = self.W
        y  = self.START_Y

        for text, style in shown_lines:
            if style == "gap":
                y += self.LINE_GAP // 2
                continue
            surf = self.fonts['medium'].render(text, True, DIM_COL)
            self.screen.blit(surf, ((W - surf.get_width()) // 2, y))
            y += self.LINE_GAP

        # Current line being typed
        if current_index < len(BRIEFING):
            text, _ = BRIEFING[current_index]
            if text:
                partial = text[:int(char_progress)]
                surf    = self.fonts['medium'].render(partial, True, TEXT_COL)
                self.screen.blit(surf, ((W - surf.get_width()) // 2, y))

                # Blinking cursor
                if (pygame.time.get_ticks() // 500) % 2 == 0:
                    cursor = self.fonts['medium'].render("▌", True, TEXT_COL)
                    self.screen.blit(cursor, (
                        (W - surf.get_width()) // 2 + surf.get_width(),
                        y
                    ))

    def _draw_footer(self, text_done, loader):
        W, H = self.W, self.H

        # Thin rule
        pygame.draw.line(self.screen, LINE_COL,
                         (60, H - 50), (W - 60, H - 50), 1)

        # Status
        if loader and not loader.is_ready():
            dots = "." * (int(pygame.time.get_ticks() / 400) % 4)
            status = f"Preparing patient records{dots}"
            col    = DIM_COL
        elif text_done:
            status = "SPACE  —  begin shift"
            col    = (120, 118, 90)
        else:
            status = ""
            col    = DIM_COL

        if status:
            s = self.fonts['small'].render(status, True, col)
            self.screen.blit(s, ((W - s.get_width()) // 2, H - 34))