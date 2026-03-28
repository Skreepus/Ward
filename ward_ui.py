import pygame
import sys
import os
import textwrap

# ── CONFIG ──────────────────────────────────────────────────────────────
W, H          = 1280, 720
PANEL_H       = int(H * 0.27)          # black bottom panel height
IMG_H         = H - PANEL_H            # top image area
FPS           = 60

BLACK         = (0,   0,   0)
NEAR_BLACK    = (8,   8,   8)
OFF_WHITE     = (210, 210, 205)
MUTED         = (120, 120, 115)
ACCENT        = (148, 148, 72)          # olive-yellow — clinical warmth
DANGER        = (175, 38,  38)
DIM_OVERLAY   = (0,   0,   0,  140)    # semi-transparent

PANEL_BORDER  = (38,  38,  38)
CARD_BG       = (14,  14,  14)
CARD_BORDER   = (48,  48,  48)
CARD_SEL      = (38,  38,  22)         # selected card tint
CARD_SEL_BDR  = (148, 148, 72)

FONT_MONO     = "couriernew"           # fallback chain handled below

pygame.init()

# ── FONT HELPERS ────────────────────────────────────────────────────────
def load_font(size, bold=False):
    for name in ["Courier New", "Courier", "couriernew", "monospace"]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

FONT_SM   = load_font(14)
FONT_MED  = load_font(17)
FONT_LG   = load_font(20, bold=True)
FONT_XL   = load_font(26, bold=True)
FONT_TIME = load_font(15)

# ── FAKE GAME STATE (replace with real data) ─────────────────────────────
PATIENTS = [
    {
        "name": "Ruth Calloway",
        "age": 67,
        "condition": "Bowel perforation",
        "severity": 8,
        "survivability": 72,
        "quote": "I'm sorry for all the fuss.",
        "returning": False,
        "flag": None,
    },
    {
        "name": "Daniel Marsh",
        "age": 44,
        "condition": "Ruptured appendix",
        "severity": 6,
        "survivability": 88,
        "quote": "I have a tax filing due Friday.",
        "returning": False,
        "flag": "donor",
    },
    {
        "name": "Priya Nair",
        "age": 19,
        "condition": "Internal haemorrhage",
        "severity": 9,
        "survivability": 61,
        "quote": "Can someone water my plants?",
        "returning": False,
        "flag": None,
    },
]

# ── TYPEWRITER ───────────────────────────────────────────────────────────
class Typewriter:
    def __init__(self, text, cps=42):
        self.full   = text
        self.cps    = cps
        self.elapsed = 0.0
        self.done   = False

    def update(self, dt):
        if not self.done:
            self.elapsed += dt
            if self.elapsed * self.cps >= len(self.full):
                self.done = True

    def text(self):
        return self.full[:int(self.elapsed * self.cps)]

    def skip(self):
        self.elapsed = len(self.full) / self.cps
        self.done = True


# ── PATIENT CARD ──────────────────────────────────────────────────────────
CARD_W = 340
CARD_H = 250
CARD_PAD = 16

def draw_patient_card(surf, x, y, patient, selected=False, index=1):
    bg  = CARD_SEL     if selected else CARD_BG
    bdr = CARD_SEL_BDR if selected else CARD_BORDER

    pygame.draw.rect(surf, bg,  (x, y, CARD_W, CARD_H))
    pygame.draw.rect(surf, bdr, (x, y, CARD_W, CARD_H), 1)

    cx = x + CARD_PAD
    cy = y + CARD_PAD

    # key number
    num_col = ACCENT if selected else MUTED
    num = FONT_LG.render(f"[{index}]", True, num_col)
    surf.blit(num, (cx, cy))

    # returning patient indicator
    if patient.get("returning"):
        ret = FONT_SM.render("← RETURNING", True, DANGER)
        surf.blit(ret, (x + CARD_W - ret.get_width() - CARD_PAD, cy + 3))

    cy += 28

    # name + age
    name_surf = FONT_LG.render(f"{patient['name']}, {patient['age']}", True, OFF_WHITE)
    surf.blit(name_surf, (cx, cy))
    cy += 24

    # condition
    cond_surf = FONT_MED.render(patient["condition"], True, MUTED)
    surf.blit(cond_surf, (cx, cy))
    cy += 26

    # divider
    pygame.draw.line(surf, CARD_BORDER, (cx, cy), (x + CARD_W - CARD_PAD, cy), 1)
    cy += 10

    # severity bar (10 blocks)
    sev_label = FONT_SM.render("SEVERITY", True, MUTED)
    surf.blit(sev_label, (cx, cy))
    cy += 16
    for i in range(10):
        col = DANGER if i < patient["severity"] else (30, 30, 30)
        pygame.draw.rect(surf, col, (cx + i * 24, cy, 20, 7))
    cy += 18

    # survivability
    pct     = patient["survivability"]
    pct_col = (80, 160, 80) if pct >= 75 else (ACCENT if pct >= 50 else DANGER)
    pct_surf = FONT_MED.render(f"{pct}%  survival w/ treatment", True, pct_col)
    surf.blit(pct_surf, (cx, cy))
    cy += 30

    # quote — wrap if long
    quote = f'"{patient["quote"]}"'
    wrapped = textwrap.wrap(quote, width=36)
    for line in wrapped[:2]:
        q_surf = FONT_SM.render(line, True, (185, 185, 155))
        surf.blit(q_surf, (cx, cy))
        cy += 17

    # social flag
    if patient.get("flag") == "donor":
        flag_surf = FONT_SM.render("▲ HOSPITAL DONOR", True, (100, 100, 60))
        surf.blit(flag_surf, (cx, y + CARD_H - CARD_PAD - 14))


# ── BOTTOM PANEL ──────────────────────────────────────────────────────────
def draw_panel(surf, rect, prompt_tw, selected, round_num, total_rounds, time_str):
    px, py, pw, ph = rect

    # panel bg + top border
    pygame.draw.rect(surf, NEAR_BLACK, rect)
    pygame.draw.line(surf, ACCENT, (px, py), (px + pw, py), 1)

    lx = px + 32
    ly = py + 16

    # status line
    status = f"ROUND {round_num}/{total_rounds}   ·   {time_str}   ·   ONE THEATRE AVAILABLE"
    st_surf = FONT_TIME.render(status, True, MUTED)
    surf.blit(st_surf, (lx, ly))
    ly += 22

    # thin divider
    pygame.draw.line(surf, PANEL_BORDER, (lx, ly), (px + pw - 32, ly), 1)
    ly += 12

    # typewriter prompt text
    prompt_text = prompt_tw.text()
    lines = textwrap.wrap(prompt_text, width=90)
    for line in lines[:3]:
        line_surf = FONT_MED.render(line, True, OFF_WHITE)
        surf.blit(line_surf, (lx, ly))
        ly += 22

    # blink cursor while typewriting
    if not prompt_tw.done:
        blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
        if blink_on:
            cursor = FONT_MED.render("▌", True, ACCENT)
            last_w = FONT_MED.size(lines[-1])[0] if lines else 0
            surf.blit(cursor, (lx + last_w, ly - 22))

    # action buttons
    by = py + ph - 44
    labels = [
        (f"[1] {PATIENTS[0]['name'].split()[0]}", 0),
        (f"[2] {PATIENTS[1]['name'].split()[0]}", 1),
        (f"[3] {PATIENTS[2]['name'].split()[0]}", 2),
    ]
    bx = lx
    for label, idx in labels:
        is_sel = (selected == idx)
        b_col  = ACCENT     if is_sel else PANEL_BORDER
        t_col  = NEAR_BLACK if is_sel else MUTED
        bw     = 160
        pygame.draw.rect(surf, b_col, (bx, by, bw, 28))
        b_surf = FONT_MED.render(label, True, t_col if is_sel else OFF_WHITE)
        surf.blit(b_surf, (bx + 10, by + 6))
        bx += bw + 12

    # confirm hint
    if selected is not None:
        conf = FONT_SM.render("ENTER  —  confirm", True, ACCENT)
        surf.blit(conf, (bx + 8, by + 8))


# ── MAIN ──────────────────────────────────────────────────────────────────
def main():
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("WARD")
    clock  = pygame.time.Clock()

    # load hospital image
    img_path = "hospitalpixel1.png"
    raw_img  = pygame.image.load(img_path).convert()
    img      = pygame.transform.scale(raw_img, (W, IMG_H))

    # dim overlay surface
    dim = pygame.Surface((W, IMG_H), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 110))

    panel_rect = (0, IMG_H, W, PANEL_H)

    prompt = Typewriter(
        "Three patients are waiting. One theatre is available. "
        "Review each case carefully. Press 1, 2 or 3 to select a patient, "
        "then ENTER to send them to surgery."
    )

    selected     = None
    round_num    = 1
    total_rounds = 6

    # card layout — centred with even gaps
    total_cards_w = 3 * CARD_W + 2 * 28
    card_start_x  = (W - total_cards_w) // 2
    card_y        = (IMG_H - CARD_H) // 2 + 10

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_1:
                    selected = 0
                if event.key == pygame.K_2:
                    selected = 1
                if event.key == pygame.K_3:
                    selected = 2
                if event.key == pygame.K_SPACE:
                    prompt.skip()
                if event.key == pygame.K_RETURN and selected is not None:
                    print(f"Chose patient: {PATIENTS[selected]['name']}")

        prompt.update(dt)

        # ── DRAW ──
        # 1. hospital image
        screen.blit(img, (0, 0))

        # 2. dim overlay on image
        screen.blit(dim, (0, 0))

        # 3. time display top-left
        time_surf = FONT_TIME.render("07:24", True, (200, 200, 200))
        screen.blit(time_surf, (32, 20))
        ward_surf = FONT_TIME.render("WARD B  —  GENERAL SURGERY", True, MUTED)
        screen.blit(ward_surf, (32, 38))

        # 4. patient cards over image
        for i, patient in enumerate(PATIENTS):
            cx = card_start_x + i * (CARD_W + 28)
            draw_patient_card(screen, cx, card_y, patient,
                              selected=(selected == i), index=i + 1)

        # 5. bottom panel
        draw_panel(screen, panel_rect, prompt, selected,
                   round_num, total_rounds, "07:24")

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
