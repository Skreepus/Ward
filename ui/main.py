import pygame
import sys
import os
import random
import threading
from .config import W, H, IMG_H, PANEL_H, FPS, DIM_OVERLAY, MUTED, CARD_W, CARD_H
from .fonts import init_fonts
from .typewriter import Typewriter
from .patient_card import draw_patient_card
from .panel import draw_panel
from .title_screen import TitleScreen
from .minigame import SurgeryMinigame
from .family_overlay import FamilyOverlay
from .ending_screen import EndingScreen
from .loading_screen import LoadingScreen
from .surgery_loading_screen import SurgeryLoadingScreen

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.systems.round_manager import RoundManager
from src.systems.outcome_manager import OutcomeTracker
from src.systems.ending_detector import EndingDetector

# ============================================
# DEBUG SETTINGS
# ============================================

SKIP_LOADING_SCREEN = False   


TITLE_BG = "title_screen.png"
WARD_BG  = "hospital4pixel.png"


class RoundLoader:
    def __init__(self):
        self.ready    = False
        self.patients = None

    def set_ready(self, patients):
        self.ready    = True
        self.patients = patients

    def is_ready(self):
        return self.ready


def _load_next_round_async(round_manager, result_container):
    try:
        patients = round_manager.start_round()
        result_container.append(("ok", patients))
    except Exception as e:
        result_container.append(("err", e))


def _start_game_with_loading(screen, fonts, round_manager, outcome_tracker):
    round_manager.start_game()
    loader = RoundLoader()

    def load_first_round():
        try:
            patients = round_manager.start_round()
            loader.set_ready(patients)
            print(f"[Main] First round loaded with {len(patients)} patients")
        except Exception as e:
            print(f"[Main] Error loading first round: {e}")
            loader.set_ready([])

    load_thread = threading.Thread(target=load_first_round, daemon=True)
    load_thread.start()

    if not SKIP_LOADING_SCREEN:
        loading = LoadingScreen(screen, fonts)
        loading.run(loader)
    else:
        print("[Main] Skipping loading screen (debug mode)")
        while not loader.is_ready():
            pygame.time.wait(100)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    return loader.patients


def _run_surgery(screen, fonts, chosen):
    pygame.event.clear()
    print(f"[Surgery] Starting surgery for patient: {chosen.get('name')}")
    mg              = SurgeryMinigame(screen, fonts, chosen)
    minigame_passed = mg.run()
    print(f"[Surgery] Minigame returned: {minigame_passed}")
    pygame.event.clear()
    return 0, minigame_passed


def _trigger_ending(screen, fonts, outcome_tracker, round_manager, family_moments_shown):
    """Detect and show the ending screen. Returns 'quit' or 'menu'."""
    patient_summary = round_manager.patient_generator.get_summary()
    total_deaths    = len(patient_summary.get("dead", []))

    ending_detector = EndingDetector(
        outcome_tracker,
        round_manager.pressure,
        patient_summary,
        total_deaths=total_deaths,
    )
    ending_data = ending_detector.detect()
    print(f"[Main] Ending determined: {ending_data['title']}")

    try:
        ending_screen = EndingScreen(screen, fonts, ending_data)
        return ending_screen.run()
    except Exception as e:
        print(f"[Main] ERROR showing ending screen: {e}")
        import traceback
        traceback.print_exc()
        # Fallback — wait for any keypress
        waiting = True
        while waiting:
            for ev in pygame.event.get():
                if ev.type in (pygame.QUIT, pygame.KEYDOWN):
                    waiting = False
        return "menu"


def _advance_round(round_num, background_thread, next_round_container, round_manager):
    """Wait for background load, return new patients and incremented round number."""
    if background_thread:
        background_thread.join()

    if next_round_container and next_round_container[0][0] == "ok":
        current_patients = next_round_container[0][1]
    else:
        current_patients = round_manager.start_round()

    round_num += 1
    print(f"[Main] Round {round_num} loaded with {len(current_patients)} patients")
    return current_patients, round_num


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("WARD")
    clock  = pygame.time.Clock()
    fonts  = init_fonts()

    if SKIP_LOADING_SCREEN:
        print("[Main] DEBUG MODE: Loading screen disabled")

    # ── Outer restart loop ────────────────────────────────────────────────
    while True:

        # ── Title screen ──────────────────────────────────────────────────
        choice = TitleScreen(screen, fonts, bg_path=TITLE_BG).run()
        if choice == 'quit':
            pygame.quit()
            sys.exit()

        # ── Game init ─────────────────────────────────────────────────────
        round_manager    = RoundManager()
        outcome_tracker  = OutcomeTracker()
        current_patients = _start_game_with_loading(
            screen, fonts, round_manager, outcome_tracker)

        selected_patient       = None
        round_num              = 1
        total_rounds           = 6
        active_overlay         = None
        in_surgery             = False
        family_moments_shown   = 0
        waiting_for_round_load = False
        next_round_container   = None
        background_thread      = None

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

        # ── Game loop ─────────────────────────────────────────────────────
        running     = True
        game_result = "menu"   # 'menu' or 'quit'

        while running:
            dt = clock.tick(FPS) / 1000.0

            # ── Overlay update ────────────────────────────────────────────
            if active_overlay:
                active_overlay.update(dt)
                if active_overlay.done:
                    active_overlay = None
                    if waiting_for_round_load:
                        waiting_for_round_load = False
                        current_patients, round_num = _advance_round(
                            round_num, background_thread,
                            next_round_container, round_manager
                        )
                        selected_patient     = None
                        in_surgery           = False
                        next_round_container = None
                        background_thread    = None
                        prompt = Typewriter(
                            f"Round {round_num}. New patients have arrived. "
                            "Click on a patient card or press 1, 2 or 3 to select, "
                            "then ENTER to confirm."
                        )

            # ── Events ───────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_result = "quit"
                    running     = False
                    break

                if active_overlay:
                    active_overlay.handle_event(event)
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not in_surgery:
                        mouse_pos = pygame.mouse.get_pos()
                        for i, card_rect in enumerate(card_rects):
                            if card_rect.collidepoint(mouse_pos) and i < len(current_patients):
                                selected_patient = i

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not in_surgery:
                        prompt.skip()

                    if event.key == pygame.K_ESCAPE and not in_surgery:
                        running = False
                        break

                    if not in_surgery:
                        if event.key == pygame.K_1 and len(current_patients) >= 1: selected_patient = 0
                        if event.key == pygame.K_2 and len(current_patients) >= 2: selected_patient = 1
                        if event.key == pygame.K_3 and len(current_patients) >= 3: selected_patient = 2

                    if event.key == pygame.K_RETURN and selected_patient is not None and not in_surgery:
                        in_surgery = True
                        chosen     = current_patients[selected_patient]
                        passed     = [p for i, p in enumerate(current_patients) if i != selected_patient]
                        print(f"[Main] Selected patient: {chosen['name']}")

                        # Surgery loading flash
                        surgery_loading = SurgeryLoadingScreen(
                            screen, fonts,
                            patient_name=chosen.get('name'),
                            duration=1.5
                        )
                        surgery_loading.run()

                        result = round_manager.submit_choice(chosen['id'])

                        # Start loading next round in background
                        next_round_container = []
                        if not round_manager.is_game_over():
                            background_thread = threading.Thread(
                                target=_load_next_round_async,
                                args=(round_manager, next_round_container),
                                daemon=True
                            )
                            background_thread.start()
                        else:
                            background_thread = None

                        # Run surgery minigame
                        wrong_clicks, minigame_passed = _run_surgery(screen, fonts, chosen)

                        effective_surv = chosen['survivability']
                        effective_surv = max(5, effective_surv - (wrong_clicks * 8))
                        if not minigame_passed:
                            effective_surv = max(5, effective_surv - 18)
                        survived = random.random() * 100 < effective_surv

                        outcome_tracker.record(
                            round_number    = round_num,
                            chosen_patient  = chosen,
                            passed_patients = passed,
                            survived        = survived,
                            minigame_failed = not minigame_passed,
                        )
                        round_manager.resolve_surgery(survived, chosen['id'])

                        # Family overlay
                        family_patient = result.get('family_patient')
                        family_line    = result.get('family_line')

                        if family_patient and family_line:
                            family_moments_shown += 1
                            print(f"[Main] Family overlay for {family_patient.get('name')}")
                            active_overlay         = FamilyOverlay(screen, fonts, family_patient, family_line)
                            waiting_for_round_load = True
                        else:
                            # No overlay — advance immediately
                            if round_manager.is_game_over():
                                game_result = _trigger_ending(
                                    screen, fonts, outcome_tracker,
                                    round_manager, family_moments_shown
                                )
                                running = False
                                break

                            current_patients, round_num = _advance_round(
                                round_num, background_thread,
                                next_round_container, round_manager
                            )
                            selected_patient     = None
                            in_surgery           = False
                            next_round_container = None
                            background_thread    = None
                            prompt = Typewriter(
                                f"Round {round_num}. New patients have arrived. "
                                "Click on a patient card or press 1, 2 or 3 to select, "
                                "then ENTER to confirm."
                            )
                            continue

                        # Check game over after overlay is set
                        if round_manager.is_game_over():
                            # Let overlay finish, then show ending
                            # We handle this when overlay.done fires above
                            pass

                        selected_patient = None
                        in_surgery       = False

            if not running:
                break

            if not active_overlay:
                prompt.update(dt)

            # ── Draw ──────────────────────────────────────────────────────
            screen.blit(img, (0, 0))
            screen.blit(dim, (0, 0))

            time_remaining = round_manager.time_remaining()
            time_str = f"{int(time_remaining // 60):02d}:{int(time_remaining % 60):02d}"

            time_surf = fonts['time'].render(time_str, True, (200, 200, 200))
            screen.blit(time_surf, (32, 20))
            ward_surf = fonts['time'].render("WARD B  \u2013  GENERAL SURGERY", True, MUTED)
            screen.blit(ward_surf, (32, 38))

            mouse_pos = pygame.mouse.get_pos()
            for i, patient in enumerate(current_patients):
                cx         = card_start_x + i * (CARD_W + 28)
                is_hovered = card_rects[i].collidepoint(mouse_pos)
                draw_patient_card(
                    screen, cx, card_y, patient,
                    selected=(selected_patient == i),
                    index=i + 1, fonts=fonts, hovered=is_hovered
                )

            draw_panel(
                screen, panel_rect, prompt, selected_patient,
                round_num, total_rounds, time_str, fonts=fonts,
                current_patients=current_patients
            )

            if active_overlay:
                active_overlay.draw()

            pygame.display.flip()

        # ── End of game loop ──────────────────────────────────────────────
        if game_result == "quit":
            pygame.quit()
            sys.exit()
        # 'menu' loops back to title


if __name__ == "__main__":
    main()