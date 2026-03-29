import time
import random
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import NUM_ROUNDS, ROUND_DURATION, TOTAL_RUNTIME
from src.systems.patient_generator import PatientGenerator
from src.systems.api_client import generate_family_moment


class RoundManager:
    def __init__(self):
        self.current_round = 0
        self.game_start_time = None
        self.round_start_time = None
        self.patient_generator = PatientGenerator()
        self.current_patients = []
        self.decisions = []          # list of {round, chosen_id, passed_ids}
        self.pressure = 0            # accumulates when social_weight patients are passed
        self.family_queue = []       # pending family moment lines to show
        self.game_over = False

    # ------------------------------------------------------------------
    # Core round flow
    # ------------------------------------------------------------------

    def start_game(self):
        self.game_start_time = time.time()
        self.current_round = 0

    def start_round(self) -> list:
        """
        Advances to the next round.
        Returns the list of patients for this round.
        """
        self.current_round += 1
        self.round_start_time = time.time()
        print(f"[RoundManager] Starting round {self.current_round}/{NUM_ROUNDS}")
        self.current_patients = self.patient_generator.get_round_patients(self.current_round)
        return self.current_patients

    def submit_choice(self, chosen_id: str) -> dict:
        """
        Player has chosen a patient to treat.
        Returns a result dict with outcome info and possible family moment.
        """
        passed_ids = [p['id'] for p in self.current_patients if p['id'] != chosen_id]
        chosen_patient = next(p for p in self.current_patients if p['id'] == chosen_id)

        # Track pressure from passed social_weight patients
        for p in self.current_patients:
            if p['id'] != chosen_id and p.get('social_weight', False):
                self.pressure += 1
                print(f"[RoundManager] Pressure +1 from passing {p['name']} (total: {self.pressure})")

        # Record decision
        self.decisions.append({
            "round": self.current_round,
            "chosen_id": chosen_id,
            "chosen_name": chosen_patient['name'],
            "passed_ids": passed_ids,
        })

        # Update patient generator
        self.patient_generator.resolve_round(chosen_id, self.current_patients)

        # Generate family moment (returns (patient, line) or None)
        family_info = self._maybe_generate_family_moment(chosen_patient, passed_ids)
        family_patient = None
        family_line = None
        if family_info:
            family_patient, family_line = family_info

        return {
            "chosen_patient": chosen_patient,
            "family_patient": family_patient,   # <-- which patient the family belongs to
            "family_line": family_line,         # <-- the line of dialogue
            "pressure": self.pressure,
            "round": self.current_round,
        }

    def resolve_surgery(self, survived: bool, patient_id: str):
        """Called after minigame resolves — marks patient dead if they didn't make it."""
        if not survived:
            self.patient_generator.mark_dead(patient_id)

    def is_game_over(self) -> bool:
        """True if all rounds done or total time exceeded."""
        time_exceeded = (time.time() - self.game_start_time) >= TOTAL_RUNTIME
        rounds_done = self.current_round >= NUM_ROUNDS
        return time_exceeded or rounds_done

    def time_remaining(self) -> float:
        """Seconds left in the total game."""
        if not self.game_start_time:
            return TOTAL_RUNTIME
        return max(0, TOTAL_RUNTIME - (time.time() - self.game_start_time))

    def round_time_remaining(self) -> float:
        """Seconds left in the current round."""
        if not self.round_start_time:
            return ROUND_DURATION
        return max(0, ROUND_DURATION - (time.time() - self.round_start_time))

    # ------------------------------------------------------------------
    # Family moment
    # ------------------------------------------------------------------

    def _maybe_generate_family_moment(self, chosen_patient: dict, passed_ids: list) -> tuple | None:
        """Returns (patient, line) or None if no moment is triggered."""
        if False:  
            return None

        waiting = self.patient_generator.waiting
        if not waiting:
            return None

        target = random.choice(waiting)

        treated_ids = [p['id'] for p in self.patient_generator.treated]
        dead_ids = [p['id'] for p in self.patient_generator.dead]

        if target['id'] in treated_ids:
            status = "treated"
        elif target['id'] in dead_ids:
            status = "died"
        elif target['id'] in passed_ids:
            status = "passed_over"
        else:
            status = "waiting"

        print(f"[RoundManager] Generating family moment for {target['name']} ({status})...")
        line = generate_family_moment(target, status)
        return (target, line)
    # ------------------------------------------------------------------
    # Summary for ending detector
    # ------------------------------------------------------------------

    def get_game_summary(self) -> dict:
        return {
            "decisions": self.decisions,
            "pressure": self.pressure,
            "rounds_played": self.current_round,
            "patient_summary": self.patient_generator.get_summary(),
        }