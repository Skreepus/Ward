"""
abdomen_minigame.py — SUTURE LINE
===================================

Abdominal surgery closure minigame.
Player must click and drag along 3 suture patterns.

Controls: Hold left mouse button and drag along the glowing path.
Press P to skip the minigame (for testing).
Press ENTER to continue after result screen.
"""

import pygame
import math
import sys
from .base import BaseMinigame

# ── Palette ───────────────────────────────────────────────────────────────
BG_COL          = (12,  8,   6)
TISSUE_COL      = (95,  45,  45)
TISSUE_DARK     = (65,  28,  28)
TISSUE_LIGHT    = (130, 62,  55)
WOUND_COL       = (40,  18,  18)
WOUND_EDGE      = (80,  35,  35)
PATH_GLOW       = (148, 148, 72,  90)
PATH_DOT        = (180, 180, 90)
PATH_DOT_DIM    = (80,  80,  40)
STITCH_COL      = (210, 210, 160)
STITCH_GLOW     = (255, 255, 200)
STITCH_DONE     = (160, 200, 130)
NEEDLE_COL      = (200, 210, 200)
PERFECT_COL     = (60,  220, 100)
GOOD_COL        = (200, 190, 60)
ACCEPTABLE_COL  = (148, 148, 72)
FAIL_COL        = (200, 50,  50)
TEXT_COL        = (160, 160, 150)
MUTED_COL       = (80,  80,  70)
ACCENT_COL      = (148, 148, 72)

# ── Constants ─────────────────────────────────────────────────────────────
TOTAL_PATTERNS      = 3
PERFECT_THRESHOLD   = 0.90    # 90%+ = PERFECT
GOOD_THRESHOLD      = 0.65    # 65-89% = GOOD
PASS_THRESHOLD      = 0.50    # 50-64% = ACCEPTABLE
FAIL_THRESHOLD      = 0.50    # below 50% = immediate FAIL
PATH_POINTS         = 180
SAMPLE_RADIUS       = 28
COMPLETION_FRAC     = 0.90


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


def _dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def _nearest_dist(point, path_points):
    if not path_points:
        return SAMPLE_RADIUS
    return min(_dist(point, p) for p in path_points)


# ── Path generators ────────────────────────────────────────────────────────

def _make_running_stitch(cx, cy, w, h):
    pts = []
    for i in range(PATH_POINTS):
        t = i / (PATH_POINTS - 1)
        x = cx - w // 2 + int(t * w)
        y = cy
        pts.append((x, y))
    return pts


def _make_mattress_stitch(cx, cy, w, h):
    pts = []
    segs = 8
    amp = h * 0.28
    for i in range(PATH_POINTS):
        t = i / (PATH_POINTS - 1)
        x = cx - w // 2 + t * w
        phase = (t * segs) % 1.0
        if phase < 0.5:
            y = cy - amp + phase * 2 * amp * 2
        else:
            y = cy + amp - (phase - 0.5) * 2 * amp * 2
        pts.append((int(x), int(y)))
    return pts


def _make_curved_closure(cx, cy, w, h):
    pts = []
    for i in range(PATH_POINTS):
        t = i / (PATH_POINTS - 1)
        x = cx - w // 2 + int(t * w)
        y = cy + int(math.sin(t * math.pi * 2) * h * 0.22)
        pts.append((x, y))
    return pts


PATTERN_DEFS = [
    {"name": "RUNNING STITCH", "generator": _make_running_stitch, "difficulty": 1},
    {"name": "MATTRESS STITCH", "difficulty": 2, "generator": _make_mattress_stitch},
    {"name": "CURVED CLOSURE", "difficulty": 3, "generator": _make_curved_closure},
]


def _get_accuracy_rating(acc):
    """Return (text, color) for accuracy rating"""
    if acc >= PERFECT_THRESHOLD:
        return "PERFECT", PERFECT_COL
    elif acc >= GOOD_THRESHOLD:
        return "GOOD", GOOD_COL
    elif acc >= PASS_THRESHOLD:
        return "ACCEPTABLE", ACCEPTABLE_COL
    else:
        return "FAIL", FAIL_COL


class AbdomenMinigame(BaseMinigame):

    def __init__(self, screen, fonts, patient, region="abdomen"):
        super().__init__(screen, fonts, patient, region)
        self.W, self.H = screen.get_size()

        self._wound_cx = self.W // 2
        self._wound_cy = int(self.H * 0.48)
        self._wound_w = int(self.W * 0.60)
        self._wound_h = int(self.H * 0.16)

        self._pattern_index = 0
        self._path = []
        self._traced = []
        self._is_dragging = False
        self._accuracies = []
        self._flash_timer = 0.0
        self._flash_text = ""
        self._flash_col = PERFECT_COL
        self._pattern_done = False
        self._transition_t = 0.0
        self.result = None
        self._skip_pressed = False
        self._should_exit = False

        # Animation states
        self.anim_state = None
        self.title_anim = None
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
        self._cutscene_printed = False

        self._game_fade_alpha = 255
        self._fade_surf = pygame.Surface((self.W, self.H))
        self._fade_surf.fill((0, 0, 0))

        self._load_pattern(0)

    def _load_pattern(self, index):
        defn = PATTERN_DEFS[index]
        self._path = defn["generator"](self._wound_cx, self._wound_cy, self._wound_w, self._wound_h)
        self._traced = []
        self._is_dragging = False
        self._pattern_done = False
        self._prog_cursor = 0

    def _progress(self):
        if not self._traced or not self._path:
            return 0.0
        n = len(self._path)
        if not hasattr(self, '_prog_cursor'):
            self._prog_cursor = 0
        last = self._traced[-1]
        search_end = min(n, self._prog_cursor + max(1, n // 8))
        best_i = self._prog_cursor
        best_d = _dist(last, self._path[self._prog_cursor])
        for i in range(self._prog_cursor, search_end):
            d = _dist(last, self._path[i])
            if d < best_d:
                best_d = d
                best_i = i
        self._prog_cursor = max(self._prog_cursor, best_i)
        return self._prog_cursor / (n - 1)

    def _evaluate_accuracy(self):
        if len(self._traced) < 10:
            return 0.0
        total = 0.0
        for pt in self._traced:
            d = _nearest_dist(pt, self._path)
            score = max(0.0, 1.0 - d / SAMPLE_RADIUS)
            total += score
        return total / len(self._traced)

    def _complete_pattern(self):
        acc = self._evaluate_accuracy()
        
        # Check if this pattern failed (below FAIL_THRESHOLD)
        if acc < FAIL_THRESHOLD:
            self._flash_text = f"FAILED — {int(acc*100)}%"
            self._flash_col = FAIL_COL
            self._flash_timer = 1.2
            self.result = False  # Immediate failure
            print(f"[AbdomenMinigame] Pattern {self._pattern_index + 1} FAILED! Accuracy: {acc:.0%}")
            return
        
        # Store the accuracy for completed patterns
        self._accuracies.append(acc)
        
        rating_text, rating_color = _get_accuracy_rating(acc)
        self._flash_text = f"{rating_text} — {int(acc*100)}%"
        self._flash_col = rating_color
        self._flash_timer = 0.8
        self._pattern_done = True
        self._transition_t = 1.2
        print(f"[AbdomenMinigame] Pattern {self._pattern_index + 1} completed. Accuracy: {acc:.0%}")

    def _skip_minigame(self):
        self._skip_pressed = True
        print("[AbdomenMinigame] Skip pressed - forcing success")
        self.result = True

    def run(self) -> bool:
        clock = pygame.time.Clock()
        pygame.mouse.set_visible(False)
        self.anim_state = None
        self.waiting_for_continue = False
        self._skip_pressed = False
        self._should_exit = False

        try:
            while True:
                dt = clock.tick(60) / 1000.0
                self._handle_events()

                # Check if we should exit due to ENTER on return_text screen
                if self._should_exit:
                    print(f"[AbdomenMinigame] Exiting via ENTER. Result: {self.result}")
                    return self.result

                if self.result is None:
                    self._update_game(dt)

                if self.result is not None and not self.anim_state:
                    self.anim_state = "title"
                    self._setup_title_animation()
                    self.title_complete = False
                    print(f"[AbdomenMinigame] Result={self.result}. Starting title animation.")

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

                # Auto-continue timers
                if self.anim_state == "subtitle" and self.waiting_for_continue:
                    if pygame.time.get_ticks() - self.auto_continue_timer >= self.auto_continue_delay:
                        self.anim_state = "fade_out"
                        self.fade_target = 0
                        self.waiting_for_continue = False
                        self.continue_prompt_visible = False

                if self.anim_state == "return_text" and self.waiting_for_continue:
                    if pygame.time.get_ticks() - self.auto_continue_timer >= self.auto_continue_delay:
                        print("[AbdomenMinigame] Auto-advance timeout")
                        return self.result

                self._draw()
                pygame.display.flip()
        finally:
            pygame.mouse.set_visible(True)

    def _setup_title_animation(self):
        if self.result:
            self.title_text = "PATIENT STABILIZED"
            self.title_color = (60, 200, 80)
        else:
            self.title_text = "COMPLICATIONS OCCURRED"
            self.title_color = (180, 40, 40)
        self.title_anim = TypewriterText(self.title_text, self.fonts['xlarge'], self.title_color, speed=20)
        self.fade_alpha = 255
        self.fade_target = 255

    def _setup_subtitle(self):
        if self.result:
            self.subtitle_text = "You feel proud, yet you may not rest. There are still other patients waiting for you."
        else:
            self.subtitle_text = "A difficult outcome. You carry the weight. Yet there are still other patients waiting for you."
        self.waiting_for_continue = True
        self.continue_prompt_visible = True
        self.auto_continue_timer = pygame.time.get_ticks()

    def _setup_return_text(self):
        self.return_anim = TypewriterText("You return to the emergency ward", self.fonts['large'], (148, 148, 72), speed=22)
        self.fade_target = 255

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.mouse.set_visible(True)
                pygame.quit()
                sys.exit()

            # Skip minigame with P (only during gameplay)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                if self.result is None and not self.anim_state and not self._pattern_done:
                    self._skip_minigame()
                    return

            # Handle continue during result screen
            if self.waiting_for_continue:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    print(f"[AbdomenMinigame] Continue key pressed. Current state: {self.anim_state}")
                    if self.anim_state == "subtitle":
                        self.anim_state = "fade_out"
                        self.fade_target = 0
                        self.waiting_for_continue = False
                        self.continue_prompt_visible = False
                        print("[AbdomenMinigame] Subtitle screen - starting fade out")
                    elif self.anim_state == "return_text":
                        print("[AbdomenMinigame] Return text screen - exiting minigame")
                        pygame.mouse.set_visible(True)
                        self._should_exit = True
                    return

            if self.anim_state is not None:
                continue

            if self.result is not None or self._pattern_done:
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._is_dragging = True
                self._traced = []
                self._prog_cursor = 0
                self._traced.append(event.pos)

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self._is_dragging:
                    self._is_dragging = False
                    self._traced.append(event.pos)
                    if self._progress() >= COMPLETION_FRAC:
                        self._complete_pattern()

            if event.type == pygame.MOUSEMOTION and self._is_dragging:
                self._traced.append(event.pos)

    def _update_game(self, dt):
        if self._game_fade_alpha > 0:
            self._game_fade_alpha = max(0, self._game_fade_alpha - 320 * dt)

        if self._flash_timer > 0:
            self._flash_timer -= dt

        if self._pattern_done:
            self._transition_t -= dt
            if self._transition_t <= 0:
                self._pattern_index += 1
                if self._pattern_index >= TOTAL_PATTERNS:
                    # All patterns completed without failure
                    if len(self._accuracies) >= TOTAL_PATTERNS:
                        self.result = True  # Success if all patterns passed
                        avg = sum(self._accuracies) / len(self._accuracies)
                        print(f"[AbdomenMinigame] All patterns passed! Avg accuracy: {avg:.0%}, Result: {self.result}")
                    else:
                        self.result = False
                else:
                    self._load_pattern(self._pattern_index)

    def _draw(self):
        self.screen.fill(BG_COL)

        if not self.anim_state:
            self._draw_wound()
            self._draw_guide_path()
            self._draw_trace()
            self._draw_needle_cursor()
            self._draw_ui()
            self._draw_accuracy_meters()
            self._draw_instructions()

        if self._game_fade_alpha > 0 and not self.anim_state:
            self._fade_surf.set_alpha(int(self._game_fade_alpha))
            self.screen.blit(self._fade_surf, (0, 0))

        # Result overlay
        if self.anim_state:
            overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))

            if self.title_anim and self.anim_state in ["title", "subtitle", "fade_out"]:
                self.title_anim.draw(self.screen, self.W // 2, self.H // 2 - 100, center_x=True)

            if self.anim_state in ["subtitle", "fade_out"] and self.subtitle_text:
                words = self.subtitle_text.split()
                lines = []
                current_line = []
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    test_surf = self.fonts['medium'].render(test_line, True, TEXT_COL)
                    if test_surf.get_width() <= self.W - 100:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(' '.join(current_line))
                y_offset = self.H // 2 - 20
                for line in lines:
                    line_surf = self.fonts['medium'].render(line, True, TEXT_COL)
                    line_rect = line_surf.get_rect(center=(self.W // 2, y_offset))
                    self.screen.blit(line_surf, line_rect)
                    y_offset += 35

            if self.anim_state == "return_text" and self.return_anim:
                self.return_anim.draw(self.screen, self.W // 2, self.H // 2, center_x=True)

            if self.continue_prompt_visible:
                prompt_text = "Press ENTER to continue"
                prompt_surf = self.fonts['medium'].render(prompt_text, True, MUTED_COL)
                prompt_rect = prompt_surf.get_rect(center=(self.W // 2, self.H - 70))
                pulse = abs(math.sin(pygame.time.get_ticks() / 500))
                prompt_surf.set_alpha(int(150 + 105 * pulse))
                self.screen.blit(prompt_surf, prompt_rect)

        if self.anim_state == "fade_out" and self.fade_alpha < 255:
            fade_overlay = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            fade_overlay.fill((0, 0, 0, int(255 - self.fade_alpha)))
            self.screen.blit(fade_overlay, (0, 0))
            if self.fade_alpha == 0:
                self.anim_state = "return_text"
                self._setup_return_text()

    def _draw_wound(self):
        cx, cy, w, h = self._wound_cx, self._wound_cy, self._wound_w, self._wound_h
        tissue_rect = pygame.Rect(cx - w // 2 - 80, cy - h - 60, w + 160, h * 2 + 120)
        pygame.draw.rect(self.screen, TISSUE_COL, tissue_rect, border_radius=30)
        pygame.draw.rect(self.screen, TISSUE_LIGHT, (tissue_rect.x + 8, tissue_rect.y + 8, tissue_rect.w - 16, 18), border_radius=12)
        for dy in range(-h, h + 60, 14):
            ty = cy + dy
            if tissue_rect.top < ty < tissue_rect.bottom:
                pygame.draw.line(self.screen, TISSUE_DARK, (tissue_rect.x + 12, ty), (tissue_rect.right - 12, ty), 1)
        wound_surf = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(wound_surf, (*WOUND_COL, 255), (0, 0, w + 20, h + 20))
        self.screen.blit(wound_surf, (cx - w // 2 - 10, cy - h // 2 - 10))
        pygame.draw.ellipse(self.screen, WOUND_EDGE, (cx - w // 2 - 10, cy - h // 2 - 10, w + 20, h + 20), 4)
        for i in range(1, 4):
            t = i / 4
            iw = int(w * (1 - t * 0.4))
            ih = int(h * (1 - t * 0.5))
            col = tuple(int(c * (1 - t * 0.4)) for c in WOUND_COL)
            pygame.draw.ellipse(self.screen, col, (cx - iw // 2, cy - ih // 2, iw, ih), 1)
        for i in range(self._pattern_index):
            self._draw_completed_stitch_indicator(i)

    def _draw_completed_stitch_indicator(self, pattern_idx):
        defn = PATTERN_DEFS[pattern_idx]
        path = defn["generator"](self._wound_cx, self._wound_cy, self._wound_w, self._wound_h)
        acc = self._accuracies[pattern_idx] if pattern_idx < len(self._accuracies) else 0.9
        col = STITCH_DONE if acc >= PASS_THRESHOLD else GOOD_COL
        step = max(1, len(path) // 30)
        for i in range(0, len(path) - step, step * 2):
            p1 = path[i]
            p2 = path[min(i + step, len(path) - 1)]
            pygame.draw.line(self.screen, col, p1, p2, 2)

    def _draw_guide_path(self):
        if not self._path or self._pattern_done:
            return
        progress = self._progress()
        for i, pt in enumerate(self._path):
            t_frac = i / (len(self._path) - 1)
            if t_frac < progress - 0.05:
                col, radius = PATH_DOT_DIM, 2
            else:
                pulse = abs(math.sin(pygame.time.get_ticks() / 300 + i * 0.1))
                bright = int(90 + 90 * pulse)
                col = (bright, bright, int(bright * 0.55))
                radius = 3 if i % 3 == 0 else 2
            if i % 3 == 0:
                pygame.draw.circle(self.screen, col, pt, radius)
        if len(self._path) > 1:
            glow_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            for i in range(0, len(self._path) - 1, 4):
                p1 = self._path[i]
                p2 = self._path[i + 1]
                t = i / len(self._path)
                if t > progress + 0.02:
                    pygame.draw.line(glow_surf, PATH_GLOW, p1, p2, 12)
            self.screen.blit(glow_surf, (0, 0))
        if self._path:
            pygame.draw.circle(self.screen, ACCENT_COL, self._path[0], 6)
            pygame.draw.circle(self.screen, (80, 80, 40), self._path[0], 6, 1)
            pygame.draw.circle(self.screen, PERFECT_COL, self._path[-1], 6)
            pygame.draw.circle(self.screen, (40, 100, 50), self._path[-1], 6, 1)

    def _draw_trace(self):
        if len(self._traced) < 2:
            return
        pygame.draw.lines(self.screen, STITCH_COL, False, self._traced, 2)
        if len(self._traced) > 4:
            pygame.draw.lines(self.screen, STITCH_GLOW, False, self._traced[-5:], 2)
        for i in range(0, len(self._traced), 40):
            if i < len(self._traced):
                pygame.draw.circle(self.screen, STITCH_COL, self._traced[i], 3)

    def _draw_needle_cursor(self):
        if self._pattern_done or self.result is not None or self.anim_state:
            return
        mx, my = pygame.mouse.get_pos()
        angle = math.radians(-35)
        length = 22
        ex = mx + int(math.cos(angle) * length)
        ey = my + int(math.sin(angle) * length)
        pygame.draw.line(self.screen, NEEDLE_COL, (mx, my), (ex, ey), 2)
        pygame.draw.circle(self.screen, NEEDLE_COL, (mx, my), 3)
        pygame.draw.circle(self.screen, BG_COL, (mx, my), 2)
        pygame.draw.circle(self.screen, STITCH_GLOW, (ex, ey), 2)
        if len(self._traced) > 1:
            pygame.draw.line(self.screen, STITCH_COL, (mx, my), self._traced[-1], 1)

    def _draw_accuracy_meters(self):
        W = self.W
        bx, by = W - 36, 20
        dot_r, spacing = 8, 22
        for i in range(TOTAL_PATTERNS):
            cx = bx - (TOTAL_PATTERNS - 1 - i) * spacing
            cy = by + dot_r
            if i < len(self._accuracies):
                acc = self._accuracies[i]
                if acc >= PERFECT_THRESHOLD:
                    col = PERFECT_COL
                elif acc >= GOOD_THRESHOLD:
                    col = GOOD_COL
                elif acc >= PASS_THRESHOLD:
                    col = ACCEPTABLE_COL
                else:
                    col = FAIL_COL
                pygame.draw.circle(self.screen, col, (cx, cy), dot_r)
            elif i == self._pattern_index and self.result is None:
                pulse = abs(math.sin(pygame.time.get_ticks() / 350))
                r = int(ACCENT_COL[0] * (0.5 + 0.5 * pulse))
                g = int(ACCENT_COL[1] * (0.5 + 0.5 * pulse))
                b = int(ACCENT_COL[2] * (0.5 + 0.5 * pulse))
                pygame.draw.circle(self.screen, (r, g, b), (cx, cy), dot_r)
            else:
                pygame.draw.circle(self.screen, (30, 30, 25), (cx, cy), dot_r)
            pygame.draw.circle(self.screen, MUTED_COL, (cx, cy), dot_r, 1)
        lbl = self.fonts['severity'].render("SUTURES", True, MUTED_COL)
        self.screen.blit(lbl, (bx - TOTAL_PATTERNS * spacing - lbl.get_width() + 4, by))
        if self._is_dragging and self._traced and not self.anim_state:
            live_acc = self._evaluate_accuracy()
            if live_acc >= PERFECT_THRESHOLD:
                col = PERFECT_COL
            elif live_acc >= GOOD_THRESHOLD:
                col = GOOD_COL
            elif live_acc >= PASS_THRESHOLD:
                col = ACCEPTABLE_COL
            else:
                col = FAIL_COL
            acc_s = self.fonts['large'].render(f"{int(live_acc * 100)}%", True, col)
            self.screen.blit(acc_s, (W - acc_s.get_width() - 36, by + dot_r * 2 + 10))
            sublbl = self.fonts['severity'].render("ACCURACY", True, MUTED_COL)
            self.screen.blit(sublbl, (W - sublbl.get_width() - 36, by + dot_r * 2 + 40))

    def _draw_ui(self):
        W, H = self.W, self.H
        p = self.patient
        if self.anim_state:
            return
        self.screen.blit(self.fonts['large'].render(f"{p['name']}, {p['age']}", True, TEXT_COL), (36, 20))
        self.screen.blit(self.fonts['small'].render(p['condition'], True, MUTED_COL), (36, 48))
        reg = self.fonts['small'].render("OPERATING: ABDOMEN", True, ACCENT_COL)
        self.screen.blit(reg, (W - reg.get_width() - 36, H - 48))
        if not self._pattern_done and self.result is None:
            defn = PATTERN_DEFS[self._pattern_index]
            pip_x, pip_y = 36, H - 52
            for i in range(3):
                col = ACCENT_COL if i < defn['difficulty'] else (35, 35, 28)
                pygame.draw.rect(self.screen, col, (pip_x + i * 14, pip_y, 10, 6), border_radius=2)
            name_s = self.fonts['medium'].render(defn['name'], True, ACCENT_COL)
            self.screen.blit(name_s, (36, H - 42))
        prog_s = self.fonts['small'].render(f"PATTERN  {self._pattern_index + 1} / {TOTAL_PATTERNS}", True, MUTED_COL)
        self.screen.blit(prog_s, (36, 76))
        if self._pattern_done and self.result is None and not self.anim_state:
            if self._pattern_index + 1 < TOTAL_PATTERNS:
                msg = f"Next: {PATTERN_DEFS[self._pattern_index + 1]['name']}..."
            else:
                msg = "Closing wound..."
            msg_s = self.fonts['medium'].render(msg, True, ACCENT_COL)
            self.screen.blit(msg_s, ((W - msg_s.get_width()) // 2, self._wound_cy - self._wound_h - 48))
        if self._flash_timer > 0 and not self.anim_state:
            alpha = int(255 * min(1.0, self._flash_timer / 0.4))
            fs = self.fonts['large'].render(self._flash_text, True, self._flash_col)
            fs.set_alpha(alpha)
            self.screen.blit(fs, ((W - fs.get_width()) // 2, self._wound_cy + self._wound_h // 2 + 30))

    def _draw_instructions(self):
        if self._pattern_done or self.result is not None or self.anim_state:
            return
        W, H = self.W, self.H
        inst_text = "Click and hold left mouse button. Drag along the glowing path to suture."
        inst_surf = self.fonts['medium'].render(inst_text, True, ACCENT_COL)
        bg_rect = pygame.Rect((W - inst_surf.get_width()) // 2 - 10, H - 80, inst_surf.get_width() + 20, 32)
        pygame.draw.rect(self.screen, (0, 0, 0, 150), bg_rect, border_radius=4)
        pygame.draw.rect(self.screen, ACCENT_COL, bg_rect, 1, border_radius=4)
        self.screen.blit(inst_surf, ((W - inst_surf.get_width()) // 2, H - 75))
        skip_text = "Press P to skip minigame"
        skip_surf = self.fonts['small'].render(skip_text, True, MUTED_COL)
        self.screen.blit(skip_surf, ((W - skip_surf.get_width()) // 2, H - 45))