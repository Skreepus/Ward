import pygame
import math
import random
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from ui.config import W, H, ACCENT, DANGER, OFF_WHITE, MUTED, NEAR_BLACK


# ── Colours ───────────────────────────────────────────────────────────────
ZONE_IDLE    = (80,  160, 80,  60)   # green tint when reticle is outside
ZONE_HIT     = (80,  200, 80,  120)  # brighter when inside
RETICLE_COL  = (220, 220, 200)
RETICLE_DIM  = (120, 120, 110)
PROGRESS_COL = (80,  200, 80)
PROGRESS_BG  = (30,  30,  28)
FAIL_COL     = DANGER
LABEL_COL    = (160, 160, 150)


class SurgeryMinigame:
    """
    Steady-hands minigame.

    The reticle drifts across the screen. Hold it inside the target zone
    to accumulate 'steady time'. Reach REQUIRED_STEADY seconds to pass.

    Total window = TOTAL_TIME seconds — long enough to mask background API calls.
    Severity (1-10) scales drift speed and jitter.

    Usage:
        mg = SurgeryMinigame(screen, fonts, patient)
        result = mg.run()   # blocks — returns True (pass) or False (fail)
    """

    TOTAL_TIME      = 10.0   # total seconds before minigame ends
    REQUIRED_STEADY =  3.0   # cumulative seconds needed inside zone to pass

    ZONE_RADIUS     = 38     # target zone radius in px
    RETICLE_RADIUS  = 18     # reticle inner circle radius

    def __init__(self, screen, fonts, patient: dict):
        self.screen  = screen
        self.fonts   = fonts
        self.patient = patient

        severity = patient.get("severity", 5)

        # Drift speed scales with severity
        base_speed    = 55 + severity * 14     # px/sec base movement speed
        self.speed    = base_speed
        self.jitter   = severity * 0.6         # random nudge per frame

        # Reticle starts near centre
        self.rx = float(W // 2 + random.randint(-60, 60))
        self.ry = float(H // 2 + random.randint(-40, 40))

        # Drift direction — changes smoothly
        angle         = random.uniform(0, math.pi * 2)
        self.dx       = math.cos(angle)
        self.dy       = math.sin(angle)
        self.turn_acc = 0.0    # accumulates to trigger direction nudge

        # Zone — fixed in centre
        self.zx = W // 2
        self.zy = int(H * 0.46)

        # Timers
        self.time_left   = self.TOTAL_TIME
        self.steady_time = 0.0
        self.inside      = False

        # Result
        self.result = None   # True = pass, False = fail

        # Fade in
        self._fade_alpha = 255
        self._fade_surf  = pygame.Surface((W, H))
        self._fade_surf.fill((0, 0, 0))

        # Pulse for zone
        self._pulse = 0.0

    # ── Main blocking run ─────────────────────────────────────────────────

    def run(self) -> bool:
        clock = pygame.time.Clock()

        while self.result is None:
            dt = clock.tick(60) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

        # Brief result flash
        self._show_result()
        return self.result

    # ── Event handling ────────────────────────────────────────────────────

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # No player input needed — purely reaction to mouse position

    # ── Update ────────────────────────────────────────────────────────────

    def _update(self, dt: float):
        # Fade in
        if self._fade_alpha > 0:
            self._fade_alpha = max(0, self._fade_alpha - 400 * dt)

        # Move reticle
        self._move_reticle(dt)

        # Check if reticle is inside zone
        dist = math.hypot(self.rx - self.zx, self.ry - self.zy)
        self.inside = dist < (self.ZONE_RADIUS - self.RETICLE_RADIUS)

        # Accumulate steady time
        if self.inside:
            self.steady_time += dt

        # Countdown
        self.time_left -= dt
        self._pulse     = (self._pulse + dt * 3) % (math.pi * 2)

        # Check end conditions
        if self.steady_time >= self.REQUIRED_STEADY:
            self.result = True
        elif self.time_left <= 0:
            self.result = False

    def _move_reticle(self, dt: float):
        """Smooth drifting movement with random direction nudges."""
        # Accumulate turn
        self.turn_acc += dt
        if self.turn_acc > random.uniform(0.4, 1.2):
            self.turn_acc = 0.0
            turn = random.uniform(-1.1, 1.1)
            angle = math.atan2(self.dy, self.dx) + turn
            self.dx = math.cos(angle)
            self.dy = math.sin(angle)

        # Jitter
        jx = random.uniform(-self.jitter, self.jitter)
        jy = random.uniform(-self.jitter, self.jitter)

        # Move
        self.rx += (self.dx * self.speed + jx) * dt
        self.ry += (self.dy * self.speed + jy) * dt

        # Bounce off edges (with margin)
        margin = 80
        if self.rx < margin:
            self.rx = margin; self.dx = abs(self.dx)
        if self.rx > W - margin:
            self.rx = W - margin; self.dx = -abs(self.dx)
        if self.ry < margin:
            self.ry = margin; self.dy = abs(self.dy)
        if self.ry > H - margin:
            self.ry = H - margin; self.dy = -abs(self.dy)

    # ── Draw ──────────────────────────────────────────────────────────────

    def _draw(self):
        self.screen.fill((8, 8, 8))
        self._draw_header()
        self._draw_zone()
        self._draw_reticle()
        self._draw_progress()
        self._draw_timer()

        # Fade in overlay
        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(int(self._fade_alpha))
            self.screen.blit(self._fade_surf, (0, 0))

    def _draw_header(self):
        patient = self.patient
        name    = f"{patient['name']}, {patient['age']}"
        cond    = patient['condition']

        title = self.fonts['large'].render("SURGERY IN PROGRESS", True, MUTED)
        self.screen.blit(title, ((W - title.get_width()) // 2, 36))

        n_surf = self.fonts['medium'].render(name, True, OFF_WHITE)
        self.screen.blit(n_surf, ((W - n_surf.get_width()) // 2, 68))

        c_surf = self.fonts['small'].render(cond, True, MUTED)
        self.screen.blit(c_surf, ((W - c_surf.get_width()) // 2, 90))

        # Instruction
        inst = self.fonts['small'].render(
            "Hold the reticle inside the zone.", True, (100, 100, 90))
        self.screen.blit(inst, ((W - inst.get_width()) // 2, H - 44))

    def _draw_zone(self):
        pulse_r = self.ZONE_RADIUS + int(math.sin(self._pulse) * 3)

        # Zone fill
        zone_surf = pygame.Surface((pulse_r * 2 + 4, pulse_r * 2 + 4), pygame.SRCALPHA)
        col = ZONE_HIT if self.inside else ZONE_IDLE
        pygame.draw.circle(zone_surf, col,
                           (pulse_r + 2, pulse_r + 2), pulse_r)
        self.screen.blit(zone_surf,
                         (self.zx - pulse_r - 2, self.zy - pulse_r - 2))

        # Zone border
        border_col = (80, 200, 80) if self.inside else (60, 100, 60)
        pygame.draw.circle(self.screen, border_col,
                           (self.zx, self.zy), pulse_r, 1)

        # Crosshair inside zone
        ch_col = (60, 120, 60)
        pygame.draw.line(self.screen, ch_col,
                         (self.zx - pulse_r, self.zy),
                         (self.zx + pulse_r, self.zy), 1)
        pygame.draw.line(self.screen, ch_col,
                         (self.zx, self.zy - pulse_r),
                         (self.zx, self.zy + pulse_r), 1)

    def _draw_reticle(self):
        rx, ry = int(self.rx), int(self.ry)
        col    = RETICLE_COL if self.inside else RETICLE_DIM
        r      = self.RETICLE_RADIUS

        # Outer circle
        pygame.draw.circle(self.screen, col, (rx, ry), r, 1)

        # Inner dot
        pygame.draw.circle(self.screen, col, (rx, ry), 3)

        # Crosshair arms (gap in centre)
        gap = 6
        pygame.draw.line(self.screen, col, (rx - r, ry), (rx - gap, ry), 1)
        pygame.draw.line(self.screen, col, (rx + gap, ry), (rx + r, ry), 1)
        pygame.draw.line(self.screen, col, (rx, ry - r), (rx, ry - gap), 1)
        pygame.draw.line(self.screen, col, (rx, ry + gap), (rx, ry + r), 1)

    def _draw_progress(self):
        """Steady time progress bar."""
        bw     = 320
        bh     = 8
        bx     = (W - bw) // 2
        by     = self.zy + self.ZONE_RADIUS + 28

        # Label
        pct    = min(self.steady_time / self.REQUIRED_STEADY, 1.0)
        label  = self.fonts['small'].render("STEADY", True, LABEL_COL)
        self.screen.blit(label, (bx, by - 18))

        # Background
        pygame.draw.rect(self.screen, PROGRESS_BG, (bx, by, bw, bh))

        # Fill
        fill_w = int(bw * pct)
        if fill_w > 0:
            pygame.draw.rect(self.screen, PROGRESS_COL, (bx, by, fill_w, bh))

        # Border
        pygame.draw.rect(self.screen, (60, 60, 55), (bx, by, bw, bh), 1)

    def _draw_timer(self):
        """Countdown timer — turns red in last 3 seconds."""
        col = FAIL_COL if self.time_left < 3.0 else MUTED
        t   = self.fonts['medium'].render(f"{self.time_left:.1f}s", True, col)
        self.screen.blit(t, (W - t.get_width() - 32, 32))

    def _show_result(self):
        """Flash pass/fail for 1.5 seconds."""
        if self.result:
            text  = "STABLE"
            color = (80, 200, 80)
        else:
            text  = "COMPLICATIONS"
            color = FAIL_COL

        end_time = pygame.time.get_ticks() + 1500
        clock    = pygame.time.Clock()

        while pygame.time.get_ticks() < end_time:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.screen.fill((8, 8, 8))

            surf = self.fonts['xlarge'].render(text, True, color)
            self.screen.blit(surf, ((W - surf.get_width()) // 2,
                                    H // 2 - surf.get_height() // 2))
            pygame.display.flip()