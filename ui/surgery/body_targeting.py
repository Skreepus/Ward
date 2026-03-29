"""
Body Targeting Phase — player clicks the correct body area.
"""
import pygame
import sys
from .body_data import BODY_HOTSPOTS

# ── Colours ───────────────────────────────────────────────────────────────
BG_DARK       = (8,   12,  10)
BODY_COL      = (55,  65,  60)
BODY_BDR      = (90,  105, 95)
HOTSPOT_IDLE  = (80,  100, 85, 100)
HOTSPOT_HOV   = (148, 148, 72, 160)
HOTSPOT_WRONG = (175, 38,  38, 180)
HOTSPOT_RIGHT = (60,  200, 80, 200)
TEXT_COL      = (160, 160, 150)
LABEL_COL     = (200, 200, 190)
MUTED_COL     = (80,  80,  70)


class BodyTargetingPhase:
    """
    Draws a draped surgery table with a simplified body outline.
    Clickable hotspots highlight on hover.
    Player must click the correct region for the patient's condition.

    Returns the number of wrong attempts.
    """

    WRONG_FLASH_DUR = 0.6

    def __init__(self, screen, fonts, patient: dict, correct_region: str):
        print(f"[BodyTargetingPhase] INITIALIZED - correct_region: {correct_region}")
        self.screen         = screen
        self.fonts          = fonts
        self.patient        = patient
        self.correct_region = correct_region
        self.W, self.H      = screen.get_size()

        # Body figure anchor
        self.fig_cx  = self.W // 2
        self.fig_top = int(self.H * 0.08)
        self.fig_h   = int(self.H * 0.78)
        self.fig_w   = int(self.fig_h * 0.38)

        # State
        self.hovered_region = None
        self.wrong_flash    = {}
        self.result_region  = None
        self.wrong_attempts = 0

        # Fade in
        self._fade_alpha = 255
        self._fade       = pygame.Surface((self.W, self.H))
        self._fade.fill((0, 0, 0))

    def _hotspot_screen_pos(self, hs):
        """Convert relative hotspot coords to screen pixels."""
        _, _, rx_frac, ry_frac, rx, ry = hs
        cx = int(self.fig_cx + (rx_frac - 0.5) * self.fig_w)
        cy = int(self.fig_top + ry_frac * self.fig_h)
        return cx, cy, rx, ry

    def _point_in_ellipse(self, px, py, cx, cy, rx, ry):
        return ((px - cx) ** 2 / rx ** 2 + (py - cy) ** 2 / ry ** 2) <= 1.0

    def run(self):
        """Blocks until correct region clicked. Returns wrong_attempts count."""
        print(f"[BodyTargetingPhase] run() STARTED")
        clock = pygame.time.Clock()

        # Flush any stale events before we start
        pygame.event.clear()

        loop_count = 0
        while self.result_region is None:
            loop_count += 1
            if loop_count % 60 == 0:  # Print every ~1 second
                print(f"[BodyTargetingPhase] Waiting for correct click... (loop {loop_count})")
            
            dt        = clock.tick(60) / 1000.0
            mouse_pos = pygame.mouse.get_pos()

            # Decay wrong flash timers
            for k in list(self.wrong_flash):
                self.wrong_flash[k] -= dt
                if self.wrong_flash[k] <= 0:
                    del self.wrong_flash[k]

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)

            # Update hover
            self.hovered_region = None
            for hs in BODY_HOTSPOTS:
                region = hs[0]
                cx, cy, rx, ry = self._hotspot_screen_pos(hs)
                if self._point_in_ellipse(*mouse_pos, cx, cy, rx, ry):
                    self.hovered_region = region
                    break

            # Fade in
            if self._fade_alpha > 0:
                self._fade_alpha = max(0, self._fade_alpha - 300 * dt)

            self._draw(mouse_pos)
            pygame.display.flip()

        print(f"[BodyTargetingPhase] EXITING - correct region clicked! Wrong attempts: {self.wrong_attempts}")
        
        # Quick visual feedback only - no extra loop
        self._flash_correct()
        
        print(f"[BodyTargetingPhase] run() COMPLETE - returning {self.wrong_attempts}")
        return self.wrong_attempts

    def _flash_correct(self):
        """Brief green flash on correct region - quick visual feedback."""
        print(f"[BodyTargetingPhase] _flash_correct() - showing green flash")
        # Find the correct hotspot
        for hs in BODY_HOTSPOTS:
            region = hs[0]
            if region == self.correct_region:
                cx, cy, rx, ry = self._hotspot_screen_pos(hs)
                
                # Draw a quick green flash
                flash_surf = pygame.Surface((rx * 2 + 8, ry * 2 + 8), pygame.SRCALPHA)
                pygame.draw.ellipse(flash_surf, (60, 200, 80, 200), 
                                   (0, 0, rx * 2 + 8, ry * 2 + 8))
                self.screen.blit(flash_surf, (cx - rx - 4, cy - ry - 4))
                pygame.display.flip()
                break
        
        # Short delay so player sees the flash
        pygame.time.wait(150)

    def _handle_click(self, pos):
        print(f"[BodyTargetingPhase] _handle_click() at {pos}")
        for hs in BODY_HOTSPOTS:
            region = hs[0]
            cx, cy, rx, ry = self._hotspot_screen_pos(hs)
            if self._point_in_ellipse(*pos, cx, cy, rx, ry):
                print(f"[BodyTargetingPhase] Clicked region: {region}, Correct region: {self.correct_region}")
                if region == self.correct_region:
                    print(f"[BodyTargetingPhase] ✓ CORRECT! Setting result_region = {region}")
                    self.result_region = region
                else:
                    print(f"[BodyTargetingPhase] ✗ WRONG! Wrong attempts +1")
                    self.wrong_flash[region] = self.WRONG_FLASH_DUR
                    self.wrong_attempts += 1
                return
        
        print(f"[BodyTargetingPhase] Click missed all hotspots")

    def _draw(self, mouse_pos):
        self.screen.fill(BG_DARK)
        self._draw_table()
        self._draw_body()
        self._draw_hotspots()
        self._draw_ui()

        if self._fade_alpha > 0:
            self._fade.set_alpha(int(self._fade_alpha))
            self.screen.blit(self._fade, (0, 0))

    def _draw_table(self):
        table_x = self.fig_cx - self.fig_w // 2 - 30
        table_w = self.fig_w + 60
        table_y = self.fig_top + 20
        table_h = self.fig_h - 20

        pygame.draw.rect(self.screen, (22, 30, 26),
                         (table_x, table_y, table_w, table_h), border_radius=8)
        pygame.draw.rect(self.screen, (35, 48, 40),
                         (table_x, table_y, table_w, table_h), 1, border_radius=8)

        for i in range(1, 6):
            dy = table_y + int(i * table_h / 6)
            pygame.draw.line(self.screen, (28, 38, 32),
                             (table_x + 8, dy), (table_x + table_w - 8, dy), 1)

    def _draw_body(self):
        cx  = self.fig_cx
        top = self.fig_top
        fh  = self.fig_h
        fw  = self.fig_w

        parts = [
            (0.50, 0.07, int(fw * 0.38), int(fh * 0.09)),   # head
            (0.50, 0.22, int(fw * 0.55), int(fh * 0.07)),   # neck/shoulder
            (0.50, 0.35, int(fw * 0.50), int(fh * 0.14)),   # chest
            (0.50, 0.50, int(fw * 0.44), int(fh * 0.10)),   # abdomen
            (0.50, 0.62, int(fw * 0.42), int(fh * 0.08)),   # pelvis
            (0.22, 0.35, int(fw * 0.16), int(fh * 0.18)),   # left arm
            (0.78, 0.35, int(fw * 0.16), int(fh * 0.18)),   # right arm
            (0.38, 0.78, int(fw * 0.18), int(fh * 0.20)),   # left leg
            (0.62, 0.78, int(fw * 0.18), int(fh * 0.20)),   # right leg
        ]

        for rx_frac, ry_frac, w, h in parts:
            ex = int(cx + (rx_frac - 0.5) * fw)
            ey = int(top + ry_frac * fh)
            pygame.draw.ellipse(self.screen, BODY_COL,
                                (ex - w, ey - h, w * 2, h * 2))
            pygame.draw.ellipse(self.screen, BODY_BDR,
                                (ex - w, ey - h, w * 2, h * 2), 1)

        # Neck connector
        neck_x = cx - int(fw * 0.08)
        neck_y = int(top + 0.10 * fh)
        neck_h = int(fh * 0.07)
        pygame.draw.rect(self.screen, BODY_COL,
                         (neck_x, neck_y, int(fw * 0.16), neck_h))

    def _draw_hotspots(self):
        for hs in BODY_HOTSPOTS:
            region, label, _, _, rx, ry = hs
            cx, cy, rx, ry = self._hotspot_screen_pos(hs)

            is_hov     = (region == self.hovered_region)
            is_wrong   = region in self.wrong_flash
            is_correct = (region == self.result_region)

            if is_correct:
                col = HOTSPOT_RIGHT
            elif is_wrong:
                t   = self.wrong_flash[region]
                col = (175, 38, 38, int(180 * (t / self.WRONG_FLASH_DUR)))
            elif is_hov:
                col = HOTSPOT_HOV
            else:
                col = HOTSPOT_IDLE

            ew, eh  = rx * 2 + 4, ry * 2 + 4
            hs_surf = pygame.Surface((ew, eh), pygame.SRCALPHA)
            pygame.draw.ellipse(hs_surf, col, (0, 0, ew, eh))
            self.screen.blit(hs_surf, (cx - rx - 2, cy - ry - 2))

            if is_hov or is_correct:
                lbl = self.fonts['small'].render(label, True, LABEL_COL)
                self.screen.blit(lbl, (cx - lbl.get_width() // 2, cy + ry + 6))

    def _draw_ui(self):
        W, H    = self.W, self.H
        patient = self.patient

        name_s = self.fonts['large'].render(
            f"{patient['name']}, {patient['age']}", True, TEXT_COL)
        self.screen.blit(name_s, (36, 20))

        cond_s = self.fonts['small'].render(patient['condition'], True, MUTED_COL)
        self.screen.blit(cond_s, (36, 48))

        if self.wrong_attempts == 0:
            inst     = "Click the correct area to begin surgery."
            inst_col = MUTED_COL
        else:
            inst     = f"Incorrect.  {self.wrong_attempts} wrong  —  condition has worsened."
            inst_col = (175, 80, 60)

        inst_s = self.fonts['medium'].render(inst, True, inst_col)
        self.screen.blit(inst_s, ((W - inst_s.get_width()) // 2, H - 36))