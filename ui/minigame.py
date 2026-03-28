import pygame
import math
import random
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


# ── Colours ───────────────────────────────────────────────────────────────
BG_COL       = (6,  10,  8)
GRID_COL     = (15, 28, 18)
LINE_COL     = (60, 220, 100)
LINE_DIM     = (30, 100,  50)
FLAT_COL     = (180, 30,  30)
TEXT_COL     = (160, 160, 150)
MUTED_COL    = (80,  80,  70)
WINDOW_COL   = (60, 220, 100, 50)   # intervention window highlight
LABEL_COL    = (100, 200, 120)


class SurgeryMinigame:
    """
    Flatline minigame.

    An ECG line scrolls continuously. The rhythm is normal at first, then
    destabilises based on severity. A critical window opens — the line
    spikes into arrhythmia. Press SPACE during the window to intervene.

    Miss it and complications occur (minigame_failed = True).
    Hit it and the patient stabilises (minigame_failed = False).

    Total duration ~10 seconds — long enough to mask background API calls.

    Usage:
        mg = SurgeryMinigame(screen, fonts, patient)
        passed = mg.run()   # blocks, returns True (pass) or False (fail)
    """

    SCROLL_SPEED   = 280      # px per second
    HISTORY_LEN    = 900      # px of ECG history to keep
    TOTAL_TIME     = 10.0     # total seconds
    WINDOW_OPEN    = 3.5      # when the critical window opens (seconds in)
    WINDOW_DURATION = 2.2     # how long the window stays open

    ECG_Y          = 0        # centre of ECG line (set in __init__)
    ECG_AMP        = 38       # normal beat amplitude
    LINE_Y         = 0        # y position of the ECG strip

    def __init__(self, screen, fonts, patient: dict):
        self.screen  = screen
        self.fonts   = fonts
        self.patient = patient

        severity         = patient.get("severity", 5)
        self.severity    = severity

        # How unstable the rhythm gets during the window
        self.instability = 0.4 + severity * 0.06   # 0.4 – 1.0

        # ECG strip sits in the middle third of the screen
        W, H             = screen.get_size()
        self.W           = W
        self.H           = H
        self.LINE_Y      = H // 2
        self.ECG_Y       = self.LINE_Y

        # Scrolling ECG buffer — list of (x_offset, y_value) relative points
        self._ecg_points = []   # raw y values, one per px
        self._scroll_acc = 0.0  # sub-pixel accumulator

        # Timers
        self.time_elapsed = 0.0
        self.result       = None   # True = pass, False = fail

        # Window state
        self._window_active  = False
        self._window_hit     = False
        self._window_elapsed = 0.0

        # Phase for ECG generation
        self._beat_phase  = 0.0
        self._beat_period = 0.72   # seconds per heartbeat (normal ~83bpm)

        # Flatline effect
        self._flatlining   = False
        self._flat_timer   = 0.0

        # Pre-fill buffer with a clean rhythm
        self._prefill()

        # Fade in
        self._fade_alpha = 255
        self._fade_surf  = pygame.Surface((W, H))
        self._fade_surf.fill((0, 0, 0))

    def _prefill(self):
        """Pre-fill ECG buffer so the line is full on first frame."""
        phase = 0.0
        for _ in range(self.HISTORY_LEN):
            phase += 1.0 / (self.SCROLL_SPEED * self._beat_period / self.W)
            self._ecg_points.append(self._ecg_sample(phase, unstable=False))

    def _ecg_sample(self, phase: float, unstable: bool) -> float:
        """
        Returns a y-offset for the ECG at the given beat phase.
        Normal = clean PQRST shape.
        Unstable = arrhythmic spikes and noise.
        """
        t = phase % 1.0   # position within one beat cycle

        if not unstable:
            # Clean PQRST approximation
            if t < 0.1:
                return math.sin(t / 0.1 * math.pi) * 8          # P wave
            elif t < 0.45:
                return 0
            elif t < 0.48:
                return -math.sin((t - 0.45) / 0.03 * math.pi) * 12   # Q
            elif t < 0.52:
                return math.sin((t - 0.48) / 0.04 * math.pi) * self.ECG_AMP  # R spike
            elif t < 0.56:
                return -math.sin((t - 0.52) / 0.04 * math.pi) * 10   # S
            elif t < 0.75:
                return math.sin((t - 0.56) / 0.19 * math.pi) * 14    # T wave
            else:
                return 0
        else:
            # Arrhythmic — irregular spikes and noise
            base = self._ecg_sample(phase, unstable=False)
            noise = random.gauss(0, self.instability * 18)
            if random.random() < 0.03 * self.instability:
                noise += random.choice([-1, 1]) * random.uniform(20, 50)
            return base + noise

    def run(self) -> bool:
        clock = pygame.time.Clock()
        while self.result is None:
            dt = clock.tick(60) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()
        self._show_result()
        return self.result

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self._window_active and not self._window_hit:
                        self._window_hit  = True
                        self._window_active = False
                        self.result       = True   # pass

    def _update(self, dt: float):
        # Fade in
        if self._fade_alpha > 0:
            self._fade_alpha = max(0, self._fade_alpha - 380 * dt)

        self.time_elapsed += dt

        # Beat phase advances with scroll
        self._beat_phase += dt / self._beat_period

        # Window logic
        in_window = (self.WINDOW_OPEN <= self.time_elapsed
                     <= self.WINDOW_OPEN + self.WINDOW_DURATION)

        if in_window and not self._window_hit:
            self._window_active   = True
            self._window_elapsed += dt
        elif self._window_active and not self._window_hit:
            # Window closed — player missed it
            self._window_active = False
            self.result         = False

        # Generate new ECG samples based on scroll speed
        self._scroll_acc += self.SCROLL_SPEED * dt
        new_samples = int(self._scroll_acc)
        self._scroll_acc -= new_samples

        for _ in range(new_samples):
            unstable = in_window and not self._window_hit
            self._ecg_points.append(
                self._ecg_sample(self._beat_phase, unstable=unstable)
            )

        # Trim buffer
        if len(self._ecg_points) > self.HISTORY_LEN:
            self._ecg_points = self._ecg_points[-self.HISTORY_LEN:]

        # Timeout
        if self.time_elapsed >= self.TOTAL_TIME and self.result is None:
            self.result = False

    def _draw(self):
        W, H = self.W, self.H

        self.screen.fill(BG_COL)
        self._draw_grid()
        self._draw_header()
        self._draw_ecg()
        self._draw_window_hint()
        self._draw_timer()

        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(int(self._fade_alpha))
            self.screen.blit(self._fade_surf, (0, 0))

    def _draw_grid(self):
        W, H = self.W, self.H
        # Faint grid lines — like a real ECG monitor
        for x in range(0, W, 40):
            pygame.draw.line(self.screen, GRID_COL, (x, 0), (x, H))
        for y in range(0, H, 40):
            pygame.draw.line(self.screen, GRID_COL, (0, y), (W, y))

    def _draw_header(self):
        W = self.W
        patient = self.patient
        name    = f"{patient['name']}, {patient['age']}"
        cond    = patient['condition']

        # Top left — patient info
        n_surf = self.fonts['large'].render(name, True, TEXT_COL)
        self.screen.blit(n_surf, (36, 28))

        c_surf = self.fonts['small'].render(cond, True, MUTED_COL)
        self.screen.blit(c_surf, (36, 54))

        # Top right — monitor label
        mon = self.fonts['small'].render("CARDIAC MONITOR", True, MUTED_COL)
        self.screen.blit(mon, (W - mon.get_width() - 36, 28))

        # Bottom instruction
        if self._window_active:
            inst = self.fonts['medium'].render(
                "INTERVENE — SPACE", True, (220, 60, 60))
        elif not self._window_hit and self.time_elapsed < self.WINDOW_OPEN:
            inst = self.fonts['small'].render(
                "Monitor the rhythm.", True, MUTED_COL)
        else:
            inst = self.fonts['small'].render("", True, MUTED_COL)

        self.screen.blit(inst, ((W - inst.get_width()) // 2, self.H - 44))

    def _draw_ecg(self):
        W      = self.W
        pts    = self._ecg_points
        n      = len(pts)
        if n < 2:
            return

        # Draw from right edge leftward
        in_window = self._window_active
        coords    = []

        for i, val in enumerate(pts):
            x = W - (n - i)
            y = int(self.ECG_Y - val)
            coords.append((x, y))

        # Colour — red during window if not yet hit
        col = FLAT_COL if in_window else LINE_COL

        pygame.draw.lines(self.screen, col, False, coords, 2)

        # Bright dot at the leading edge
        if coords:
            pygame.draw.circle(self.screen, col, coords[-1], 3)

    def _draw_window_hint(self):
        """Subtle red bar on the timeline showing where the window is."""
        W = self.W
        total = self.TOTAL_TIME
        bar_y = self.H - 14
        bar_h = 4

        # Full timeline bar
        pygame.draw.rect(self.screen, (30, 30, 28), (36, bar_y, W - 72, bar_h))

        # Window region
        wx = 36 + int((self.WINDOW_OPEN / total) * (W - 72))
        ww = int((self.WINDOW_DURATION / total) * (W - 72))
        pygame.draw.rect(self.screen, (120, 30, 30), (wx, bar_y, ww, bar_h))

        # Current position
        cx = 36 + int((min(self.time_elapsed, total) / total) * (W - 72))
        pygame.draw.rect(self.screen, TEXT_COL, (cx - 1, bar_y - 2, 2, bar_h + 4))

    def _draw_timer(self):
        W      = self.W
        t_left = max(0, self.TOTAL_TIME - self.time_elapsed)
        col    = (180, 40, 40) if self._window_active else MUTED_COL
        t_surf = self.fonts['medium'].render(f"{t_left:.1f}s", True, col)
        self.screen.blit(t_surf, (W - t_surf.get_width() - 36, 54))

    def _show_result(self):
        W, H   = self.W, self.H
        text   = "STABLE" if self.result else "COMPLICATIONS"
        colour = (60, 200, 80) if self.result else (180, 40, 40)

        end_time = pygame.time.get_ticks() + 1800
        clock    = pygame.time.Clock()

        while pygame.time.get_ticks() < end_time:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.screen.fill(BG_COL)
            self._draw_grid()
            self._draw_ecg()

            # Dark overlay
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

            surf = self.fonts['xlarge'].render(text, True, colour)
            self.screen.blit(surf, ((W - surf.get_width()) // 2,
                                    H // 2 - surf.get_height() // 2))
            pygame.display.flip()