import pygame
import sys
import math
import random
from .config import W, H, ACCENT, OFF_WHITE, BLACK, NEAR_BLACK, MUTED

# ── Swap background here or pass bg_path= to constructor ─────────────────
TITLE_BG_PATH = "hospitalpixel1.png"
TITLE_BG_CURSE = "title_screen_curse.png"  # Curse background for flicker effect

# ── Colours ───────────────────────────────────────────────────────────────
TEXT_BRIGHT   = (220, 220, 212)   # main readable text
TEXT_MED      = (170, 170, 160)   # subtitle
TEXT_DIM      = (110, 110, 102)   # hints / version
BTN_IDLE_BD   = (72,  72,  65)    # button border when not hovered
BTN_IDLE_TX   = (160, 160, 150)   # button text when not hovered
BTN_HOV_BD    = ACCENT
BTN_HOV_TX    = ACCENT
BTN_HOV_BG    = (26,  26,  16)


class FlickerTitle:
    """
    WARD rendered in a thin, elegant font with tighter letter spacing.
    Flicker effects only — no movement whatsoever.

    Effects per letter (each runs independently):
      • alpha flicker  — letter briefly dims / vanishes
      • red flash      — letter snaps to blood red for ~80ms
      • ghost double   — a faint offset copy appears briefly
    """

    # Tune these to taste — higher = more frequent
    FLICKER_PROB = 0.004    # chance per letter per frame of starting a flicker
    RED_PROB     = 0.0018   # chance per letter per frame of a red flash
    GHOST_PROB   = 0.0025   # chance per letter per frame of a ghost double

    TITLE_COLOUR = (195, 192, 145)   # warm off-white — not pure yellow
    TITLE_RED    = (190, 28,  28)
    TITLE_GHOST  = (195, 192, 145)

    def __init__(self, font):
        self.font    = font
        self.letters = list("WARD")

        # per-letter timers (seconds remaining for each effect)
        self.flicker_t = [0.0] * 4
        self.flicker_a = [255] * 4   # alpha during flicker
        self.red_t     = [0.0] * 4
        self.ghost_t   = [0.0] * 4

        # pre-render base surfaces once — letters don't move so we can cache
        self._base  = [font.render(ch, True, self.TITLE_COLOUR) for ch in self.letters]
        self._red   = [font.render(ch, True, self.TITLE_RED)    for ch in self.letters]

        # TIGHTER SPACING - reduced from 18 to 6 pixels between letters
        spacing     = 6   # Changed: was 18, now much tighter
        total_w     = sum(s.get_width() for s in self._base) + spacing * 3
        self._xs    = []
        x           = W // 2 - total_w // 2
        for s in self._base:
            self._xs.append(x)
            x += s.get_width() + spacing

        self._y     = 160   # fixed vertical position — never changes

    def update(self, dt):
        for i in range(4):
            # ── flicker ──────────────────────────────────────────────────
            if self.flicker_t[i] > 0:
                self.flicker_t[i] -= dt
                self.flicker_a[i] = random.randint(8, 60)
            else:
                self.flicker_a[i] = 255
                if random.random() < self.FLICKER_PROB:
                    self.flicker_t[i] = random.uniform(0.05, 0.18)

            # ── red flash ────────────────────────────────────────────────
            if self.red_t[i] > 0:
                self.red_t[i] -= dt
            elif random.random() < self.RED_PROB:
                self.red_t[i] = random.uniform(0.06, 0.14)

            # ── ghost double ─────────────────────────────────────────────
            if self.ghost_t[i] > 0:
                self.ghost_t[i] -= dt
            elif random.random() < self.GHOST_PROB:
                self.ghost_t[i] = random.uniform(0.04, 0.10)

    def draw(self, screen):
        for i in range(4):
            x = self._xs[i]
            y = self._y   # STATIC — no offset added

            # choose surface: red flash overrides normal
            if self.red_t[i] > 0:
                surf = self._red[i]
            else:
                surf = self._base[i]

            # ghost double — faint copy a few pixels offset, drawn first
            if self.ghost_t[i] > 0:
                ghost = self._base[i].copy()
                ghost.set_alpha(35)
                screen.blit(ghost, (x + random.randint(3, 7), y + random.randint(-2, 2)))

            # main letter
            if self.flicker_t[i] > 0:
                copy = surf.copy()
                copy.set_alpha(self.flicker_a[i])
                screen.blit(copy, (x, y))
            else:
                screen.blit(surf, (x, y))


class Button:
    W_BTN = 280
    H_BTN = 46

    def __init__(self, label, y, font):
        self.label   = label
        self.rect    = pygame.Rect((W - self.W_BTN) // 2, y, self.W_BTN, self.H_BTN)
        self.font    = font
        self.hovered = False
        self._flash  = 0.0

    def update(self, dt, mouse_pos):
        # hovered set by mouse position ONLY — never externally forced
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self._flash > 0:
            self._flash -= dt

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._flash = 0.10
                return True
        return False

    def draw(self, surf, kb_selected=False):
        flashing = self._flash > 0
        lit      = flashing or self.hovered or kb_selected

        if flashing:
            bg = TEXT_BRIGHT;  bd = TEXT_BRIGHT;  tx = NEAR_BLACK
        elif lit:
            bg = BTN_HOV_BG;   bd = BTN_HOV_BD;   tx = BTN_HOV_TX
        else:
            bg = (10, 10, 10); bd = BTN_IDLE_BD;  tx = BTN_IDLE_TX

        pygame.draw.rect(surf, bg, self.rect)
        pygame.draw.rect(surf, bd, self.rect, 1)

        ls = self.font.render(self.label, True, tx)
        lx = self.rect.x + (self.rect.w - ls.get_width())  // 2
        ly = self.rect.y + (self.rect.h - ls.get_height()) // 2
        surf.blit(ls, (lx, ly))


class TitleScreen:
    """
    Call run() — blocks until player chooses.
    Returns: 'play' | 'quit'
    """

    SUBTITLE = "A shift that does not feel short."

    CREDIT_LINES = [
        ("WARD",                             "header"),
        ("A Medical Triage Game",            "body"),
        ("",                                 "gap"),
        ("",                                 "gap"),
        ("",                                 "gap"),

        ("Game Design & Development",        "label"),
        ("Kenneth Wu -- Srineer Esarapu",                   "name"),
        ("",                                 "gap"),
        ("Built with pygame in python for Hackiethon 2026","body"),
        ("",                                 "gap"),
        ("",                                 "gap"),
        ("",                                 "gap"),
        ("",                                 "gap"),
        ("",                                 "gap"),
        ("",                                 "gap"),
        ("",                                 "gap"),
        
        ("[ ESC or click anywhere to close ]","hint"),
    ]

    def __init__(self, screen, fonts, bg_path=None, custom_font_path=None):
        self.screen = screen
        self.fonts  = fonts

        # ── title font — Special Elite ────────────────────────────────────────
        title_font = None
        
        # Load your custom font
        try:
            import os
            # Get the directory where this file is located
            current_dir = os.path.dirname(__file__)
            font_path = os.path.join(current_dir, "SpecialElite-Regular.ttf")
            
            # Load the font at 140px size
            title_font = pygame.font.Font(font_path, 140)
            print(f"Successfully loaded Special Elite font")
        except Exception as e:
            print(f"Could not load Special Elite: {e}")
            # Fallback to system font
            title_font = pygame.font.SysFont("Arial", 140, bold=False)
        
        self.title = FlickerTitle(title_font)

        # ── background with flicker effect ───────────────────────────────────
        # Load both backgrounds
        self.background_normal = None
        self.background_curse = None
        self.current_background = None
        
        # Load normal background
        path = bg_path or TITLE_BG_PATH
        try:
            raw = pygame.image.load(path).convert()
            self.background_normal = pygame.transform.scale(raw, (W, H))
            self.current_background = self.background_normal
            print(f"Loaded normal background: {path}")
        except Exception as e:
            print(f"[TitleScreen] Could not load background '{path}': {e}")
        
        # Load curse background
        try:
            import os
            current_dir = os.path.dirname(__file__)
            curse_path = os.path.join(current_dir, TITLE_BG_CURSE)
            raw_curse = pygame.image.load(curse_path).convert()
            self.background_curse = pygame.transform.scale(raw_curse, (W, H))
            print(f"Loaded curse background: {curse_path}")
        except Exception as e:
            print(f"[TitleScreen] Could not load curse background: {e}")

        # ── background flicker timer ─────────────────────────────────────────
        self.flicker_timer = 0.0
        self.flicker_interval = 10.0  # 30 seconds between flickers
        self.is_flickering = False
        self.flicker_duration = 1  # 0.2 seconds for the flicker effect
        self.flicker_elapsed = 0.0

        # dim overlay — dark enough to read text, light enough to see image
        self._dim = pygame.Surface((W, H), pygame.SRCALPHA)
        self._dim.fill((0, 0, 0, 148))

        # ── fonts for UI text ─────────────────────────────────────────────
        # use a slightly larger size for buttons so they're easier to read
        try:
            btn_font  = pygame.font.SysFont("liberationmono", 19, bold=True)
            hint_font = pygame.font.SysFont("liberationmono", 14)
            sub_font  = pygame.font.SysFont("liberationmono", 17)
        except Exception:
            btn_font  = fonts['medium']
            hint_font = fonts['small']
            sub_font  = fonts['medium']

        self._btn_font  = btn_font
        self._hint_font = hint_font
        self._sub_font  = sub_font

        # ── buttons ───────────────────────────────────────────────────────
        btn_top = 430
        gap     = 60
        self._btns = {
            'play':    Button("[ PLAY ]",    btn_top,         btn_font),
            'credits': Button("[ CREDITS ]", btn_top + gap,   btn_font),
            'quit':    Button("[ QUIT ]",    btn_top + gap*2, btn_font),
        }
        self._btn_order    = ['play', 'credits', 'quit']
        self._kb_index     = -1      # -1 = nothing selected until arrow key used
        self._using_kb     = False
        self._show_credits = False

        # fade-in
        self._fade       = pygame.Surface((W, H))
        self._fade.fill((0, 0, 0))
        self._fade_alpha = 255
        self._fade_speed = 180

    def _update_background_flicker(self, dt):
        """Update the background flicker effect"""
        if not self.is_flickering:
            # Count down to next flicker
            self.flicker_timer += dt
            if self.flicker_timer >= self.flicker_interval:
                self.is_flickering = True
                self.flicker_elapsed = 0.0
                self.flicker_timer = 0.0
                # Switch to curse background
                if self.background_curse:
                    self.current_background = self.background_curse
                print("Background flicker: CURSE")
        else:
            # During flicker
            self.flicker_elapsed += dt
            if self.flicker_elapsed >= self.flicker_duration:
                # End flicker, return to normal background
                self.is_flickering = False
                self.current_background = self.background_normal
                print("Background flicker: NORMAL")
        
    def _draw_bg(self):
        """Draw background with flicker effect"""
        if self.current_background:
            self.screen.blit(self.current_background, (0, 0))
        else:
            self.screen.fill((14, 14, 14))
        self.screen.blit(self._dim, (0, 0))

    def _draw_subtitle(self):
        # accent rule sits just below the title letters
        title_bottom = self.title._y + self.title._base[0].get_height() + 12
        lw = 420
        pygame.draw.line(self.screen, (90, 88, 60),
                         ((W - lw) // 2, title_bottom),
                         ((W + lw) // 2, title_bottom), 1)

        sub = self._sub_font.render(self.SUBTITLE, True, TEXT_MED)
        self.screen.blit(sub, ((W - sub.get_width()) // 2, title_bottom + 10))

    def _draw_hints(self):
        # keyboard hint line — brighter and slightly larger than before
        line1 = self._hint_font.render(
            "↑ ↓   navigate        ENTER   confirm        ESC   quit",
            True, TEXT_DIM)
        self.screen.blit(line1, ((W - line1.get_width()) // 2, H - 26))

        ver = self._hint_font.render("v0.1", True, (65, 65, 58))
        self.screen.blit(ver, (W - ver.get_width() - 18, H - 26))

    def _draw_credits_overlay(self):
        pw, ph = 580, 300
        px = (W - pw) // 2
        py = (H - ph) // 2

        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 215))
        self.screen.blit(shade, (0, 0))

        pygame.draw.rect(self.screen, (12, 12, 10), (px, py, pw, ph))
        pygame.draw.rect(self.screen, ACCENT,        (px, py, pw, ph), 1)

        cy = py + 28
        for text, style in self.CREDIT_LINES:
            if style == "gap":
                cy += 10
                continue
            font   = self.fonts['xlarge'] if style == "header" else \
                     self.fonts['medium'] if style == "name"   else \
                     self._hint_font
            colour = TEXT_BRIGHT         if style in ("header", "name") else \
                     ACCENT              if style == "label"             else \
                     (68, 65, 48)        if style == "hint"              else \
                     TEXT_MED
            s = font.render(text, True, colour)
            self.screen.blit(s, (px + (pw - s.get_width()) // 2, cy))
            cy += s.get_height() + 7

    # ── main loop ─────────────────────────────────────────────────────────

    def run(self):
        clock = pygame.time.Clock()

        while True:
            dt        = clock.tick(60) / 1000.0
            mouse_pos = pygame.mouse.get_pos()

            # Update background flicker
            self._update_background_flicker(dt)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return 'quit'

                # mouse movement cancels keyboard mode → only one button lit
                if event.type == pygame.MOUSEMOTION:
                    self._using_kb = False
                    self._kb_index = -1

                if event.type == pygame.KEYDOWN:
                    if self._show_credits:
                        if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                            self._show_credits = False
                        continue
                    if event.key == pygame.K_ESCAPE:
                        return 'quit'
                    if event.key in (pygame.K_UP, pygame.K_DOWN):
                        self._using_kb = True
                        if self._kb_index == -1:
                            self._kb_index = 0
                        elif event.key == pygame.K_UP:
                            self._kb_index = (self._kb_index - 1) % 3
                        else:
                            self._kb_index = (self._kb_index + 1) % 3
                    if event.key == pygame.K_RETURN and self._using_kb and self._kb_index >= 0:
                        action = self._btn_order[self._kb_index]
                        if action == 'credits':
                            self._show_credits = True
                        else:
                            return action

                if event.type == pygame.MOUSEBUTTONDOWN and self._show_credits:
                    self._show_credits = False
                    continue

                if not self._show_credits:
                    for key, btn in self._btns.items():
                        if btn.handle_event(event):
                            if key == 'credits':
                                self._show_credits = True
                            else:
                                return key

            # ── update ────────────────────────────────────────────────────
            self.title.update(dt)
            for key, btn in self._btns.items():
                btn.update(dt, mouse_pos)

            if self._fade_alpha > 0:
                self._fade_alpha = max(0, self._fade_alpha - self._fade_speed * dt)

            # ── draw ──────────────────────────────────────────────────────
            self._draw_bg()
            self.title.draw(self.screen)
            self._draw_subtitle()

            for i, key in enumerate(self._btn_order):
                kb_sel = self._using_kb and (i == self._kb_index)
                self._btns[key].draw(self.screen, kb_selected=kb_sel)

            self._draw_hints()

            if self._show_credits:
                self._draw_credits_overlay()

            if self._fade_alpha > 0:
                self._fade.set_alpha(int(self._fade_alpha))
                self.screen.blit(self._fade, (0, 0))

            pygame.display.flip()