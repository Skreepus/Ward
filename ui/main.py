import pygame
import sys
import os
import random
import threading
from .config import W, H, IMG_H, PANEL_H, FPS, DIM_OVERLAY, MUTED, CARD_W, CARD_H, ACCENT
from .fonts import init_fonts
from .typewriter import Typewriter
from .patient_card import draw_patient_card
from .panel import draw_panel
from .title_screen import TitleScreen
from .minigame import SurgeryMinigame
from .loading_screen import LoadingScreen  # Add this import

# Import backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.systems.round_manager import RoundManager
from src.systems.outcome_manager import OutcomeTracker
from src.systems.ending_detector import EndingDetector

TITLE_BG = "title_screen.png"
WARD_BG  = "hospital4pixel.png"


def _load_next_round_async(round_manager, result_container):
    """Runs in background thread. Stores patients in result_container list."""
    try:
        patients = round_manager.start_round()
        result_container.append(("ok", patients))
    except Exception as e:
        result_container.append(("err", e))


class NextRoundLoader:
    """Simple wrapper to check if loading is complete"""
    def __init__(self):
        self.ready = False
        self.patients = None
    
    def set_ready(self, patients):
        self.ready = True
        self.patients = patients
    
    def is_ready(self):
        return self.ready


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("WARD")
    clock = pygame.time.Clock()

    fonts = init_fonts()

    # ── TITLE SCREEN ──────────────────────────────────────────────────────
    choice = TitleScreen(screen, fonts, bg_path=TITLE_BG).run()
    if choice == 'quit':
        pygame.quit()
        sys.exit()

    # ── LOADING SCREEN ────────────────────────────────────────────────────
    # Create a loader that will be populated by a background thread
    loader = NextRoundLoader()
    
    # Start loading the first round in background while loading screen plays
    round_manager = RoundManager()
    outcome_tracker = OutcomeTracker()
    
    def load_first_round():
        try:
            round_manager.start_game()
            patients = round_manager.start_round()
            loader.set_ready(patients)
        except Exception as e:
            print(f"Error loading first round: {e}")
            loader.set_ready([])
    
    # Start loading in background
    load_thread = threading.Thread(target=load_first_round, daemon=True)
    load_thread.start()
    
    # Show loading screen
    loading = LoadingScreen(screen, fonts)
    loading.run(loader)  # This blocks until loading is complete
    
    # Get the loaded patients
    current_patients = loader.patients
    selected_patient = None
    round_num = 1
    total_rounds = 6

    prompt = Typewriter(
        "Three patients are waiting. One theatre is available. "
        "Review each case carefully. Click on a patient card or press 1, 2 or 3 to select, "
        "then ENTER to send them to surgery."
    )

    try:
        raw_img = pygame.image.load(WARD_BG).convert()
        img     = pygame.transform.scale(raw_img, (W, IMG_H))
    except Exception:
        img = pygame.Surface((W, IMG_H))
        img.fill((30, 30, 40))
        print(f"Warning: could not load ward background '{WARD_BG}'")

    dim        = pygame.Surface((W, IMG_H), pygame.SRCALPHA)
    dim.fill(DIM_OVERLAY)
    panel_rect = (0, IMG_H, W, PANEL_H)

    card_rects    = []
    total_cards_w = 3 * CARD_W + 2 * 32
    card_start_x  = (W - total_cards_w) // 2
    card_y        = (IMG_H - CARD_H) // 2 + 5

    for i in range(3):
        card_rects.append(pygame.Rect(
            card_start_x + i * (CARD_W + 32), card_y, CARD_W, CARD_H
        ))

    # ── GAME LOOP ─────────────────────────────────────────────────────────
    running           = True
    family_line       = None
    family_line_timer = 0

    while running:
        dt = clock.tick(FPS) / 1000.0

        if family_line_timer > 0:
            family_line_timer -= dt
            if family_line_timer <= 0:
                family_line = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for i, card_rect in enumerate(card_rects):
                    if card_rect.collidepoint(mouse_pos) and i < len(current_patients):
                        selected_patient = i

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    choice = TitleScreen(screen, fonts, bg_path=TITLE_BG).run()
                    if choice == 'quit':
                        running = False
                    elif choice == 'play':
                        selected_patient  = None
                        round_manager     = RoundManager()
                        outcome_tracker   = OutcomeTracker()
                        round_manager.start_game()
                        current_patients  = round_manager.start_round()
                        round_num         = 1
                        family_line       = None
                        family_line_timer = 0
                        prompt = Typewriter(
                            "Three patients are waiting. One theatre is available. "
                            "Review each case carefully. Click on a patient card or press 1, 2 or 3 to select, "
                            "then ENTER to send them to surgery."
                        )
                    continue

                if event.key == pygame.K_1 and len(current_patients) >= 1: selected_patient = 0
                if event.key == pygame.K_2 and len(current_patients) >= 2: selected_patient = 1
                if event.key == pygame.K_3 and len(current_patients) >= 3: selected_patient = 2
                if event.key == pygame.K_SPACE: prompt.skip()

                if event.key == pygame.K_RETURN and selected_patient is not None:
                    chosen  = current_patients[selected_patient]
                    passed  = [p for i, p in enumerate(current_patients) if i != selected_patient]

                    print(f"[Main] Selected patient: {chosen['name']}")
                    
                    # ── Submit choice to backend ──────────────────────────
                    result      = round_manager.submit_choice(chosen['id'])
                    family_line = result.get('family_line')
                    if family_line:
                        family_line_timer = 3.0

                    # ── Start loading next round in background ────────────
                    next_round_container = []
                    if not round_manager.is_game_over():
                        t = threading.Thread(
                            target=_load_next_round_async,
                            args=(round_manager, next_round_container),
                            daemon=True
                        )
                        t.start()
                    else:
                        t = None

                    # ── Run minigame (masks API latency) ──────────────────
                    print(f"[Main] Starting SurgeryMinigame...")
                    mg              = SurgeryMinigame(screen, fonts, chosen)
                    minigame_passed = mg.run()
                    print(f"[Main] SurgeryMinigame returned: {minigame_passed}")

                    # Surgery outcome — minigame result determines success
                    survived = minigame_passed

                    # ── Record outcome ────────────────────────────────────
                    outcome_tracker.record(
                        round_number    = round_num,
                        chosen_patient  = chosen,
                        passed_patients = passed,
                        survived        = survived,
                        minigame_failed = not minigame_passed,
                    )
                    round_manager.resolve_surgery(survived, chosen['id'])

                    print(f"[Main] After resolve_surgery. Round {round_num}/{total_rounds}")

                    # ── Game over? ────────────────────────────────────────
                    if round_manager.is_game_over():
                        print(f"[Main] GAME OVER!")
                        ending_detector = EndingDetector(
                            outcome_tracker,
                            round_manager.pressure,
                            round_manager.patient_generator.get_summary()
                        )
                        ending = ending_detector.detect()
                        print(f"Ending: {ending['title']}")
                        running = False
                    else:
                        # Wait for background thread if still loading
                        if t is not None:
                            t.join()

                        if next_round_container:
                            status, payload = next_round_container[0]
                            if status == "ok":
                                current_patients = payload
                            else:
                                print(f"[main] Patient load error: {payload}")
                                current_patients = round_manager.start_round()
                        else:
                            current_patients = round_manager.start_round()

                        round_num       += 1
                        selected_patient = None
                        prompt = Typewriter(
                            f"Round {round_num}. New patients have arrived. "
                            "Click on a patient card or press 1, 2 or 3 to select, "
                            "then ENTER to confirm."
                        )
                        print(f"[Main] Round {round_num} loaded with {len(current_patients)} patients")

        prompt.update(dt)

        # ── DRAW ──────────────────────────────────────────────────────────
        screen.blit(img, (0, 0))
        screen.blit(dim, (0, 0))

        time_remaining = round_manager.time_remaining()
        time_str = f"{int(time_remaining // 60):02d}:{int(time_remaining % 60):02d}"

        time_surf = fonts['time'].render(time_str, True, (200, 200, 200))
        screen.blit(time_surf, (32, 20))
        ward_surf = fonts['time'].render("WARD B  —  GENERAL SURGERY", True, MUTED)
        screen.blit(ward_surf, (32, 38))

        if family_line and family_line_timer > 0:
            family_surf = fonts['medium'].render(family_line, True, ACCENT)
            family_rect = family_surf.get_rect(center=(W // 2, 60))
            bg_rect     = pygame.Rect(family_rect.x - 10, family_rect.y - 5,
                                      family_rect.width + 20, family_rect.height + 10)
            bg_surface  = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, 180))
            screen.blit(bg_surface, bg_rect)
            screen.blit(family_surf, family_rect)

        mouse_pos = pygame.mouse.get_pos()
        for i, patient in enumerate(current_patients):
            cx         = card_start_x + i * (CARD_W + 28)
            is_hovered = card_rects[i].collidepoint(mouse_pos)
            draw_patient_card(screen, cx, card_y, patient,
                              selected=(selected_patient == i),
                              index=i + 1, fonts=fonts, hovered=is_hovered)

        draw_panel(screen, panel_rect, prompt, selected_patient,
                   round_num, total_rounds, time_str, fonts=fonts,
                   current_patients=current_patients)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()