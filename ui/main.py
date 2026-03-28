import pygame
import sys
from .config import W, H, IMG_H, PANEL_H, FPS, DIM_OVERLAY, MUTED, CARD_W, CARD_H
from .fonts import init_fonts
from .typewriter import Typewriter
from .patient_card import draw_patient_card
from .panel import draw_panel
from .title_screen import TitleScreen

# ── Swap background images here ──────────────────────────────────────────
TITLE_BG   = "title_screen.png"   # title screen background
WARD_BG    = "hospitalpixel1.png"   # ward screen background (can be different)


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("WARD")
    clock  = pygame.time.Clock()

    fonts = init_fonts()

    # ── TITLE SCREEN ──────────────────────────────────────────────────────
    # bg_path= lets you pass any image file; falls back to TITLE_BG_PATH in
    # title_screen.py if omitted.
    choice = TitleScreen(screen, fonts, bg_path=TITLE_BG).run()

    if choice == 'quit':
        pygame.quit()
        sys.exit()
    # choice == 'play' falls through to game init below

    # ── GAME INIT ─────────────────────────────────────────────────────────
    # lazy import so patients aren't needed until we actually play
    from .data.patients import PATIENTS

    try:
        raw_img = pygame.image.load(WARD_BG).convert()
        img     = pygame.transform.scale(raw_img, (W, IMG_H))
    except Exception:
        img = pygame.Surface((W, IMG_H))
        img.fill((30, 30, 40))
        print(f"Warning: could not load ward background '{WARD_BG}'")

    dim = pygame.Surface((W, IMG_H), pygame.SRCALPHA)
    dim.fill(DIM_OVERLAY)

    panel_rect = (0, IMG_H, W, PANEL_H)

    prompt = Typewriter(
        "Three patients are waiting. One theatre is available. "
        "Review each case carefully. Press 1, 2 or 3 to select a patient, "
        "then ENTER to send them to surgery."
    )

    selected     = None
    round_num    = 1
    total_rounds = 6

    total_cards_w = 3 * CARD_W + 2 * 28
    card_start_x  = (W - total_cards_w) // 2
    card_y        = (IMG_H - CARD_H) // 2 + 10

    # ── GAME LOOP ─────────────────────────────────────────────────────────
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # back to title screen
                    choice = TitleScreen(screen, fonts, bg_path=TITLE_BG).run()
                    if choice == 'quit':
                        running = False
                    elif choice == 'play':
                        selected = None
                        prompt   = Typewriter(
                            "Three patients are waiting. One theatre is available. "
                            "Review each case carefully. Press 1, 2 or 3 to select a patient, "
                            "then ENTER to send them to surgery."
                        )
                    continue

                if event.key == pygame.K_1:     selected = 0
                if event.key == pygame.K_2:     selected = 1
                if event.key == pygame.K_3:     selected = 2
                if event.key == pygame.K_SPACE: prompt.skip()
                if event.key == pygame.K_RETURN and selected is not None:
                    print(f"Chose patient: {PATIENTS[selected]['name']}")

        prompt.update(dt)

        # draw ward screen
        screen.blit(img, (0, 0))
        screen.blit(dim, (0, 0))

        time_surf = fonts['time'].render("07:24", True, (200, 200, 200))
        screen.blit(time_surf, (32, 20))
        ward_surf = fonts['time'].render("WARD B  —  GENERAL SURGERY", True, MUTED)
        screen.blit(ward_surf, (32, 38))

        for i, patient in enumerate(PATIENTS):
            cx = card_start_x + i * (CARD_W + 28)
            draw_patient_card(screen, cx, card_y, patient,
                              selected=(selected == i), index=i + 1, fonts=fonts)

        draw_panel(screen, panel_rect, prompt, selected,
                   round_num, total_rounds, "07:24", fonts=fonts)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
