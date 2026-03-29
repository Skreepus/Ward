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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.systems.round_manager import RoundManager
from src.systems.outcome_manager import OutcomeTracker
from src.systems.ending_detector import EndingDetector

TITLE_BG = "title_screen.png"
WARD_BG = "hospital4pixel.png"


def _load_next_round_async(round_manager, result_container):
    try:
        patients = round_manager.start_round()
        result_container.append(("ok", patients))
    except Exception as e:
        result_container.append(("err", e))


def _start_game(screen, fonts, round_manager, outcome_tracker):
    round_manager.start_game()
    container = []
    t = threading.Thread(
        target=_load_next_round_async,
        args=(round_manager, container),
        daemon=True
    )
    t.start()
    t.join()
    if container and container[0][0] == "ok":
        return container[0][1]
    else:
        return round_manager.start_round()


def _run_surgery(screen, fonts, chosen):
    pygame.event.clear()
    print(f"[Surgery] Starting surgery for patient: {chosen.get('name')}")
    mg = SurgeryMinigame(screen, fonts, chosen)
    minigame_passed = mg.run()
    print(f"[Surgery] Minigame returned: {minigame_passed}")
    pygame.event.clear()
    return 0, minigame_passed


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("WARD")
    clock = pygame.time.Clock()
    fonts = init_fonts()

    # Outer restart loop – returns to title screen after each game
    while True:
        # ---------- TITLE SCREEN ----------
        choice = TitleScreen(screen, fonts, bg_path=TITLE_BG).run()
        if choice == 'quit':
            pygame.quit()
            sys.exit()

        # ---------- GAME INIT ----------
        round_manager = RoundManager()
        outcome_tracker = OutcomeTracker()
        current_patients = _start_game(screen, fonts, round_manager, outcome_tracker)

        selected_patient = None
        round_num = 1
        total_rounds = 6
        active_overlay = None
        in_surgery = False
        family_moments_shown = 0
        waiting_for_round_load = False
        next_round_container = None
        background_thread = None

        prompt = Typewriter(
            "Three patients are waiting. One theatre is available. "
            "Review each case carefully. Click on a patient card or press 1, 2 or 3 to select, "
            "then ENTER to send them to surgery."
        )

        try:
            raw_img = pygame.image.load(WARD_BG).convert()
            img = pygame.transform.scale(raw_img, (W, IMG_H))
        except Exception:
            img = pygame.Surface((W, IMG_H))
            img.fill((30, 30, 40))
            print(f"Warning: could not load ward background '{WARD_BG}'")

        dim = pygame.Surface((W, IMG_H), pygame.SRCALPHA)
        dim.fill(DIM_OVERLAY)
        panel_rect = (0, IMG_H, W, PANEL_H)

        card_rects = []
        total_cards_w = 3 * CARD_W + 2 * 32
        card_start_x = (W - total_cards_w) // 2
        card_y = (IMG_H - CARD_H) // 2 + 5
        for i in range(3):
            card_rects.append(pygame.Rect(
                card_start_x + i * (CARD_W + 32), card_y, CARD_W, CARD_H
            ))

        running = True
        while running:
            dt = clock.tick(FPS) / 1000.0

            # Update overlay
            if active_overlay:
                active_overlay.update(dt)
                if active_overlay.done:
                    active_overlay = None
                    if waiting_for_round_load:
                        waiting_for_round_load = False
                        if background_thread:
                            background_thread.join()
                        if next_round_container and next_round_container[0][0] == "ok":
                            current_patients = next_round_container[0][1]
                        else:
                            current_patients = round_manager.start_round()
                        round_num += 1
                        selected_patient = None
                        in_surgery = False
                        prompt = Typewriter(
                            f"Round {round_num}. New patients have arrived. "
                            "Click on a patient card or press 1, 2 or 3 to select, "
                            "then ENTER to confirm."
                        )
                        print(f"[Main] Round {round_num} loaded with {len(current_patients)} patients")
                        next_round_container = None
                        background_thread = None

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if active_overlay:
                    active_overlay.handle_event(event)
                    continue   # block game input while overlay is active

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not in_surgery:
                        mouse_pos = pygame.mouse.get_pos()
                        for i, card_rect in enumerate(card_rects):
                            if card_rect.collidepoint(mouse_pos) and i < len(current_patients):
                                selected_patient = i

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and not in_surgery:
                        # Return to title screen immediately
                        running = False
                        break

                    if not in_surgery:
                        if event.key == pygame.K_1 and len(current_patients) >= 1:
                            selected_patient = 0
                        if event.key == pygame.K_2 and len(current_patients) >= 2:
                            selected_patient = 1
                        if event.key == pygame.K_3 and len(current_patients) >= 3:
                            selected_patient = 2
                        if event.key == pygame.K_SPACE:
                            prompt.skip()

                    if event.key == pygame.K_RETURN and selected_patient is not None and not in_surgery:
                        in_surgery = True
                        chosen = current_patients[selected_patient]
                        passed = [p for i, p in enumerate(current_patients) if i != selected_patient]
                        print(f"[Main] Selected patient: {chosen['name']}")

                        result = round_manager.submit_choice(chosen['id'])

                        # Pre-load next round in background (if game not over)
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

                        # Run surgery
                        wrong_clicks, minigame_passed = _run_surgery(screen, fonts, chosen)
                        effective_surv = chosen['survivability']
                        if not minigame_passed:
                            effective_surv = max(5, effective_surv - 18)
                        survived = random.random() * 100 < effective_surv

                        outcome_tracker.record(
                            round_number=round_num,
                            chosen_patient=chosen,
                            passed_patients=passed,
                            survived=survived,
                            minigame_failed=not minigame_passed,
                        )
                        round_manager.resolve_surgery(survived, chosen['id'])

                        # Family overlay
                        family_patient = result.get('family_patient')
                        family_line = result.get('family_line')
                        if family_patient and family_line:
                            family_moments_shown += 1
                            print(f"[Main] Creating overlay for {family_patient.get('name')}")
                            active_overlay = FamilyOverlay(screen, fonts, family_patient, family_line)
                            waiting_for_round_load = True
                        else:
                            # No overlay – proceed immediately
                            waiting_for_round_load = False
                            if background_thread:
                                background_thread.join()
                            if next_round_container and next_round_container[0][0] == "ok":
                                current_patients = next_round_container[0][1]
                            else:
                                current_patients = round_manager.start_round()
                            round_num += 1
                            selected_patient = None
                            in_surgery = False
                            prompt = Typewriter(
                                f"Round {round_num}. New patients have arrived. "
                                "Click on a patient card or press 1, 2 or 3 to select, "
                                "then ENTER to confirm."
                            )
                            print(f"[Main] Round {round_num} loaded with {len(current_patients)} patients")
                            next_round_container = None
                            background_thread = None
                            continue

                        # Check game over (after surgery, before round transition)
                        if round_manager.is_game_over():
                            print("[Main] GAME OVER!")
                            total_deaths = len(round_manager.patient_generator.dead)
                            ending_detector = EndingDetector(
                                outcome_tracker,
                                round_manager.pressure,
                                round_manager.patient_generator.get_summary(),
                                total_deaths=total_deaths,
                                family_moments=family_moments_shown
                            )
                            ending_data = ending_detector.detect()
                            ending_screen = EndingScreen(screen, fonts, ending_data)
                            ending_screen.run()
                            running = False
                            break

                        # Reset selection and surgery flag (overlay will handle round transition)
                        selected_patient = None
                        in_surgery = False

            if not running:
                break

            # Update prompt only if no overlay (optional)
            if not active_overlay:
                prompt.update(dt)

            # ---------- DRAW ----------
            screen.blit(img, (0, 0))
            screen.blit(dim, (0, 0))

            time_remaining = round_manager.time_remaining()
            time_str = f"{int(time_remaining // 60):02d}:{int(time_remaining % 60):02d}"
            time_surf = fonts['time'].render(time_str, True, (200, 200, 200))
            screen.blit(time_surf, (32, 20))
            ward_surf = fonts['time'].render("WARD B  –  GENERAL SURGERY", True, MUTED)
            screen.blit(ward_surf, (32, 38))

            mouse_pos = pygame.mouse.get_pos()
            for i, patient in enumerate(current_patients):
                cx = card_start_x + i * (CARD_W + 28)
                is_hovered = card_rects[i].collidepoint(mouse_pos)
                draw_patient_card(
                    screen, cx, card_y, patient,
                    selected=(selected_patient == i),
                    index=i+1, fonts=fonts, hovered=is_hovered
                )

            draw_panel(
                screen, panel_rect, prompt, selected_patient,
                round_num, total_rounds, time_str, fonts=fonts,
                current_patients=current_patients
            )

            if active_overlay:
                active_overlay.draw()

            pygame.display.flip()

        # End of game loop – will go back to title screen (outer while True)

if __name__ == "__main__":
    main()