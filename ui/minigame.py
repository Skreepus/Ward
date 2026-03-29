"""
minigame.py — Surgery Minigame System (Orchestrator)
=====================================================

Flow:
  1. SurgeryMinigame.run() is called from main.py
  2. BodyTargetingPhase shows surgery table with clickable body regions
  3. Correct click → launches appropriate sub-minigame for that region
  4. Returns True (pass) or False (fail)

Adding a new body-part minigame:
  - Create a class in minigames/ that inherits from BaseMinigame
  - Add it to REGION_MINIGAMES dict below
"""

import pygame
import sys
from .surgery.body_targeting import BodyTargetingPhase
from .surgery.body_data import condition_to_region
from .minigames import ECGMinigame, ReactionMinigame, SpineMinigame, ArmMinigame, LegMinigame, PelvisMinigame


# ── Region → Sub-minigame mapping ─────────────────────────────────────────
# Add new minigames here as you create them
REGION_MINIGAMES = {
    "chest": PelvisMinigame,
    "head": PelvisMinigame,
    "abdomen": PelvisMinigame,
    "pelvis": PelvisMinigame,
    "arm": PelvisMinigame,
    "spine": PelvisMinigame,
    "leg": PelvisMinigame,
}


class SurgeryMinigame:
    """
    Orchestrates the full surgery sequence:
      Phase 1 — BodyTargetingPhase  (click the correct body area)
      Phase 2 — Sub-minigame        (region-specific challenge)

    Usage (unchanged from original):
        mg = SurgeryMinigame(screen, fonts, patient)
        passed = mg.run()   # True = no complications, False = complications
    """

    def __init__(self, screen, fonts, patient: dict):
        self.screen = screen
        self.fonts = fonts
        self.patient = patient

    def run(self) -> bool:
        # ── Phase 1: body targeting ───────────────────────────────────────
        correct_region = condition_to_region(self.patient.get("condition", ""))

        targeting = BodyTargetingPhase(
            self.screen, self.fonts, self.patient, correct_region)
        wrong_attempts = targeting.run()

        # ── Brief transition flash ────────────────────────────────────────
        self._transition(correct_region)

        # ── Phase 2: sub-minigame ─────────────────────────────────────────
        # Get the appropriate minigame class for this region
        minigame_class = REGION_MINIGAMES.get(correct_region, ReactionMinigame)
        sub = minigame_class(self.screen, self.fonts, self.patient, correct_region)
        sub_result = sub.run()

        # Penalise wrong targeting clicks (2+ wrong clicks = fail)
        if wrong_attempts >= 2:
            return False
        return sub_result

    def _transition(self, region: str):
        """1-second black fade between phases with region label."""
        W, H = self.screen.get_size()
        clock = pygame.time.Clock()
        start = pygame.time.get_ticks()
        dur = 800  # ms

        while pygame.time.get_ticks() - start < dur:
            clock.tick(60)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            t = (pygame.time.get_ticks() - start) / dur
            alpha = int(255 * (1 - abs(t * 2 - 1)))  # fade in then out
            self.screen.fill((0, 0, 0))

            label = self.fonts['large'].render(
                f"OPERATING: {region.upper()}", True, (148, 148, 72))
            label.set_alpha(alpha)
            self.screen.blit(label,
                             ((W - label.get_width()) // 2,
                              H // 2 - label.get_height() // 2))
            pygame.display.flip()