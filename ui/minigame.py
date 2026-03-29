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
from .minigames import (
    ECGMinigame,
    ReactionMinigame,
    SpineMinigame,
    ArmMinigame,
    LegMinigame,
    PelvisMinigame,
    BrainPuzzleMinigame,
)


# ── Region → Sub-minigame mapping ─────────────────────────────────────────
# Add new minigames here as you create them
REGION_MINIGAMES = {
    "chest": ECGMinigame,
    "head": BrainPuzzleMinigame,
    "abdomen": ReactionMinigame,      # Replace with AbdomenMinigame when ready
    "pelvis": PelvisMinigame,
    "arm": ArmMinigame,
    "spine": SpineMinigame,
    "leg": LegMinigame,
}


class SurgeryMinigame:
    """
    Orchestrates the full surgery sequence:
      Phase 1 — BodyTargetingPhase  (click the correct body area)
      Phase 2 — Sub-minigame        (region-specific challenge)

    The patient's region is determined in this order:
      1. If patient has a "region" field from API → use it directly
      2. Otherwise, derive region from condition using condition_to_region()
    """

    def __init__(self, screen, fonts, patient: dict):
        self.screen = screen
        self.fonts = fonts
        self.patient = patient
        self._cached_region = None  # Cache the region so we don't determine it twice
        print(f"[SurgeryMinigame] __init__() - patient: {patient.get('name')}")

    def _determine_region(self) -> str:
        """
        Determine the correct body region for this patient.
        Cached so it's only calculated once.
        """
        # Return cached value if already calculated
        if self._cached_region is not None:
            print(f"[SurgeryMinigame] Using cached region: {self._cached_region}")
            return self._cached_region
        
        print(f"[SurgeryMinigame] _determine_region() called (first time)")
        
        # Check if the patient already has a region field from the API
        api_region = self.patient.get("region")
        if api_region:
            # Validate that it's a valid region
            valid_regions = ["chest", "head", "abdomen", "pelvis", "arm", "spine", "leg"]
            if api_region in valid_regions:
                print(f"[SurgeryMinigame] Using API region: {api_region}")
                self._cached_region = api_region
                return self._cached_region
            else:
                print(f"[SurgeryMinigame] Warning: Invalid API region '{api_region}', falling back to condition mapping")
        
        # Fallback: derive region from condition
        condition = self.patient.get("condition", "")
        derived_region = condition_to_region(condition)
        print(f"[SurgeryMinigame] Derived region from condition '{condition}': {derived_region}")
        self._cached_region = derived_region
        return self._cached_region

    def run(self) -> bool:
        """
        Run the full surgery sequence.
        Returns True if surgery successful, False if complications occurred.
        """
        print(f"[SurgeryMinigame] ========== run() STARTED ==========")
        
        # ── Phase 0: Determine the correct body region (ONCE) ─────────────
        correct_region = self._determine_region()
        print(f"[SurgeryMinigame] Correct region for {self.patient.get('name')}: {correct_region}")

        # ── Phase 1: Body targeting (ONLY ONCE) ───────────────────────────
        print(f"[SurgeryMinigame] Creating BodyTargetingPhase...")
        targeting = BodyTargetingPhase(
            self.screen, self.fonts, self.patient, correct_region)
        
        print(f"[SurgeryMinigame] Calling targeting.run()...")
        wrong_attempts = targeting.run()
        print(f"[SurgeryMinigame] Body targeting complete. Wrong attempts: {wrong_attempts}")

        # ── Phase 2: Brief transition flash ───────────────────────────────
        print(f"[SurgeryMinigame] Showing transition for region: {correct_region}")
        self._transition(correct_region)
        print(f"[SurgeryMinigame] Transition complete")

        # ── Phase 3: Sub-minigame (region-specific) ───────────────────────
        # Get the appropriate minigame class for this region
        minigame_class = REGION_MINIGAMES.get(correct_region, ReactionMinigame)
        print(f"[SurgeryMinigame] Launching minigame: {minigame_class.__name__}")

        # Create and run the minigame
        sub = minigame_class(self.screen, self.fonts, self.patient, correct_region)
        sub_result = sub.run()
        print(f"[SurgeryMinigame] Minigame result: {sub_result}")

        # ── Phase 4: Apply penalties for wrong targeting attempts ─────────
        # If player clicked wrong area 2 or more times, surgery fails
        if wrong_attempts >= 2:
            print(f"[SurgeryMinigame] Failed due to {wrong_attempts} wrong targeting attempts")
            return False

        print(f"[SurgeryMinigame] ========== run() COMPLETE - returning {sub_result} ==========")
        return sub_result

    def _transition(self, region: str):
        """
        Show a brief black fade transition with the region label.
        Creates a smooth visual transition between phases.
        """
        print(f"[SurgeryMinigame] _transition() - region: {region}")
        W, H = self.screen.get_size()
        clock = pygame.time.Clock()
        start = pygame.time.get_ticks()
        dur = 800  # milliseconds

        while pygame.time.get_ticks() - start < dur:
            clock.tick(60)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Calculate fade progress (fade in, then fade out)
            t = (pygame.time.get_ticks() - start) / dur
            alpha = int(255 * (1 - abs(t * 2 - 1)))  # fade in then out
            self.screen.fill((0, 0, 0))

            # Render the operating region label
            label = self.fonts['large'].render(
                f"OPERATING: {region.upper()}", True, (148, 148, 72))
            label.set_alpha(alpha)
            self.screen.blit(label,
                             ((W - label.get_width()) // 2,
                              H // 2 - label.get_height() // 2))
            pygame.display.flip()
        
        print(f"[SurgeryMinigame] _transition() complete")


# Optional: Debug function to test region mapping
def test_region_mapping():
    """
    Test function to verify that conditions map to the correct regions.
    Useful for debugging the condition-to-region mapping.
    """
    test_cases = [
        ("Ruptured Aortic Aneurysm", "chest"),
        ("Severe Asthma Attack", "chest"),
        ("Acute Appendicitis", "abdomen"),
        ("Tibia Fracture", "leg"),
        ("Herniated Disc", "spine"),
        ("Pelvic Fracture", "pelvis"),
        ("Cranial Bleed", "head"),
        ("Shoulder Dislocation", "arm"),
    ]
    
    print("Testing region mapping:")
    for condition, expected in test_cases:
        result = condition_to_region(condition)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{condition}' → {result} (expected: {expected})")