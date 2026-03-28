import pygame
import sys
import os
import random
from .config import W, H, IMG_H, PANEL_H, FPS, DIM_OVERLAY, MUTED, CARD_W, CARD_H, ACCENT  # Add ACCENT here
from .fonts import init_fonts
from .typewriter import Typewriter
from .patient_card import draw_patient_card
from .panel import draw_panel
from .title_screen import TitleScreen

# Import backend - add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.systems.round_manager import RoundManager
from src.systems.outcome_manager import OutcomeTracker
from src.systems.ending_detector import EndingDetector

# ── Swap background images here ──────────────────────────────────────────
TITLE_BG   = "title_screen.png"
WARD_BG    = "hospital4pixel.png"


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
    total_rounds = 6
    
    # Show initial prompt
    prompt = Typewriter(
        "Three patients are waiting. One theatre is available. "
        "Review each case carefully. Click on a patient card or press 1, 2 or 3 to select, "
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

    # Card layout - store card rectangles for mouse click detection
    card_rects = []
    total_cards_w = 3 * CARD_W + 2 * 32 
    card_start_x = (W - total_cards_w) // 2
    card_y = (IMG_H - CARD_H) // 2 + 5

    for i in range(3):
        card_rects.append(pygame.Rect(
            card_start_x + i * (CARD_W + 32),  # Match the gap
            card_y,
            CARD_W,
            CARD_H
        ))

    # ── GAME LOOP ─────────────────────────────────────────────────────────
    running = True
    waiting_for_surgery = False
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

            # ── MOUSE CLICK DETECTION ─────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                # Check if clicked on any patient card
                for i, card_rect in enumerate(card_rects):
                    if card_rect.collidepoint(mouse_pos) and i < len(current_patients):
                        selected_patient = i
                        print(f"Selected patient {i+1}: {current_patients[i]['name']}")

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # back to title screen
                    choice = TitleScreen(screen, fonts, bg_path=TITLE_BG).run()
                    if choice == 'quit':
                        running = False
                    elif choice == 'play':
                        # Reset everything
                        selected_patient = None
                        round_manager = RoundManager()
                        outcome_tracker = OutcomeTracker()
                        round_manager.start_game()
                        current_patients = round_manager.start_round()
                        round_num = 1
                        family_line = None
                        family_line_timer = 0
                        prompt = Typewriter(
                            "Three patients are waiting. One theatre is available. "
                            "Review each case carefully. Click on a patient card or press 1, 2 or 3 to select, "
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
                        survived = random.random() * 100 < survivability
                        minigame_failed = False
                        
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
                            # Get ending
                            ending_detector = EndingDetector(
                                outcome_tracker, 
                                round_manager.pressure,
                                round_manager.patient_generator.get_summary()
                            )
                            ending = ending_detector.detect()
                            print(f"Ending: {ending['title']}")
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
                                "Click on a patient card or press 1, 2 or 3 to select, "
                                "then ENTER to confirm."
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
            bg_rect = pygame.Rect(family_rect.x - 10, family_rect.y - 5, 
                                  family_rect.width + 20, family_rect.height + 10)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, 180))
            screen.blit(bg_surface, bg_rect)
            screen.blit(family_surf, family_rect)

        # Patient cards with mouse hover effect
        mouse_pos = pygame.mouse.get_pos()
        for i, patient in enumerate(current_patients):
            cx = card_start_x + i * (CARD_W + 28)
            # Check if mouse is hovering over this card
            is_hovered = card_rects[i].collidepoint(mouse_pos)
            # Pass hover state to card drawing (you can add a glow effect)
            draw_patient_card(screen, cx, card_y, patient,
                            selected=(selected_patient == i), 
                            index=i + 1, 
                            fonts=fonts,
                            hovered=is_hovered)

        # Bottom panel - NO BUTTONS
        draw_panel(screen, panel_rect, prompt, selected_patient,
                  round_num, total_rounds, time_str, fonts=fonts,
                  current_patients=current_patients)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()