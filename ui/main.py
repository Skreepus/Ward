import pygame
import sys
import os
from .config import W, H, IMG_H, PANEL_H, FPS, DIM_OVERLAY, MUTED, CARD_W, CARD_H
from .fonts import init_fonts
from .typewriter import Typewriter
from .patient_card import draw_patient_card
from .panel import draw_panel
from .title_screen import TitleScreen

# Import backend systems
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.systems.round_manager import RoundManager
from src.systems.outcome_manager import OutcomeTracker
from src.systems.ending_detector import EndingDetector

# ── Swap background images here ──────────────────────────────────────────
TITLE_BG   = "title_screen.png"
WARD_BG    = "hospitalpixel1.png"


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

    # ── GAME INIT ─────────────────────────────────────────────────────────
    # Initialize backend systems
    round_manager = RoundManager()
    outcome_tracker = OutcomeTracker()
    
    # Start the game
    round_manager.start_game()
    
    # Load first round patients
    current_patients = round_manager.start_round()
    selected_patient = None
    round_num = 1
    total_rounds = 6  # NUM_ROUNDS from config
    
    # Show initial prompt
    prompt = Typewriter(
        "Three patients are waiting. One theatre is available. "
        "Review each case carefully. Press 1, 2 or 3 to select a patient, "
        "then ENTER to send them to surgery."
    )

    # Load background
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

    # Card layout
    total_cards_w = 3 * CARD_W + 2 * 28
    card_start_x = (W - total_cards_w) // 2
    card_y = (IMG_H - CARD_H) // 2 + 10

    # ── GAME LOOP ─────────────────────────────────────────────────────────
    running = True
    waiting_for_surgery = False
    surgery_result = None
    family_line = None
    family_line_timer = 0
    
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # Handle family line display timer
        if family_line_timer > 0:
            family_line_timer -= dt
            if family_line_timer <= 0:
                family_line = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    choice = TitleScreen(screen, fonts, bg_path=TITLE_BG).run()
                    if choice == 'quit':
                        running = False
                    else:
                        selected_patient = None
                        round_manager = RoundManager()
                        outcome_tracker = OutcomeTracker()
                        round_manager.start_game()
                        current_patients = round_manager.start_round()
                        round_num = 1
                        prompt = Typewriter(
                            "Three patients are waiting. One theatre is available. "
                            "Review each case carefully. Press 1, 2 or 3 to select a patient, "
                            "then ENTER to send them to surgery."
                        )
                    continue

                # Only handle input if not waiting for surgery result
                if not waiting_for_surgery:
                    if event.key == pygame.K_1 and len(current_patients) >= 1:
                        selected_patient = 0
                    if event.key == pygame.K_2 and len(current_patients) >= 2:
                        selected_patient = 1
                    if event.key == pygame.K_3 and len(current_patients) >= 3:
                        selected_patient = 2
                    if event.key == pygame.K_SPACE:
                        prompt.skip()
                    if event.key == pygame.K_RETURN and selected_patient is not None:
                        # Submit choice to backend
                        chosen = current_patients[selected_patient]
                        result = round_manager.submit_choice(chosen['id'])
                        family_line = result.get('family_line')
                        family_line_timer = 3.0  # Show for 3 seconds
                        
                        # Record in outcome tracker
                        passed_patients = [p for i, p in enumerate(current_patients) if i != selected_patient]
                        
                        # Simulate surgery outcome (based on survivability)
                        survivability = chosen['survivability']
                        import random
                        survived = random.random() * 100 < survivability
                        minigame_failed = False  # You can add minigame later
                        
                        outcome_tracker.record(
                            round_number=round_num,
                            chosen_patient=chosen,
                            passed_patients=passed_patients,
                            survived=survived,
                            minigame_failed=minigame_failed
                        )
                        
                        round_manager.resolve_surgery(survived, chosen['id'])
                        
                        # Check if game is over
                        if round_manager.is_game_over():
                            # Show ending screen
                            ending_detector = EndingDetector(
                                outcome_tracker, 
                                round_manager.pressure,
                                round_manager.patient_generator.get_summary()
                            )
                            ending = ending_detector.detect()
                            print(f"Ending: {ending['title']}")
                            # You'll need to create an ending screen function here
                            running = False
                        else:
                            # Load next round
                            current_patients = round_manager.start_round()
                            round_num += 1
                            selected_patient = None
                            waiting_for_surgery = False
                            # Update prompt for new round
                            prompt = Typewriter(
                                f"Round {round_num}. New patients have arrived. "
                                "Choose carefully. One theatre is still available."
                            )

        prompt.update(dt)

        # ── DRAW ──
        screen.blit(img, (0, 0))
        screen.blit(dim, (0, 0))

        # Time and location
        time_remaining = round_manager.time_remaining()
        time_str = f"{int(time_remaining // 60):02d}:{int(time_remaining % 60):02d}"
        time_surf = fonts['time'].render(time_str, True, (200, 200, 200))
        screen.blit(time_surf, (32, 20))
        ward_surf = fonts['time'].render("WARD B  —  GENERAL SURGERY", True, MUTED)
        screen.blit(ward_surf, (32, 38))

        # Display family moment if active
        if family_line and family_line_timer > 0:
            family_surf = fonts['medium'].render(family_line, True, ACCENT)
            family_rect = family_surf.get_rect(center=(W//2, 60))
            # Draw background for text
            pygame.draw.rect(screen, (0, 0, 0, 180), 
                           (family_rect.x - 10, family_rect.y - 5, 
                            family_rect.width + 20, family_rect.height + 10))
            screen.blit(family_surf, family_rect)

        # Patient cards
        for i, patient in enumerate(current_patients):
            cx = card_start_x + i * (CARD_W + 28)
            draw_patient_card(screen, cx, card_y, patient,
                            selected=(selected_patient == i), index=i + 1, fonts=fonts)

        # Bottom panel
        draw_panel(screen, panel_rect, prompt, selected_patient,
                  round_num, total_rounds, time_str, fonts=fonts)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()