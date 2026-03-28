import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.systems.api_client import generate_patients, deteriorate_patient


class PatientGenerator:
    def __init__(self):
        self.all_patients = []       # every patient seen this game
        self.waiting = []            # currently in queue
        self.treated = []            # successfully treated
        self.dead = []               # died waiting or post-surgery

    def get_round_patients(self, round_number: int) -> list:
        """
        Returns 2-3 patients for this round.
        Deteriorates any returning patients first,
        then fills remaining slots with new API-generated patients.
        """
        round_patients = []

        # Deteriorate and re-queue waiting patients (passed over last round)
        deteriorated = []
        for p in self.waiting:
            print(f"[PatientGenerator] Deteriorating {p['name']}...")
            worse = deteriorate_patient(p)
            deteriorated.append(worse)
        self.waiting = deteriorated
        round_patients.extend(self.waiting)

        # How many new patients do we need?
        slots_needed = (2 if round_number > 3 else 3) - len(round_patients)

        if slots_needed > 0:
            print(f"[PatientGenerator] Generating {slots_needed} new patients...")
            new_patients = generate_patients(
                round_number=round_number,
                existing_patients=self.all_patients
            )
            # Only take as many as we need
            new_patients = new_patients[:slots_needed]
            round_patients.extend(new_patients)
            self.all_patients.extend(new_patients)

        return round_patients

    def resolve_round(self, treated_id: str, round_patients: list):
        """
        Called after the player makes their choice.
        treated_id: the id of the patient who got the surgery slot.
        Everyone else goes into waiting (will deteriorate next round).
        """
        self.waiting = []

        for p in round_patients:
            if p['id'] == treated_id:
                self.treated.append(p)
            else:
                # Check if they've been passed over too many times
                if p.get('times_passed', 0) >= 3 or p.get('survivability', 100) <= 5:
                    print(f"[PatientGenerator] {p['name']} has died waiting.")
                    self.dead.append(p)
                else:
                    self.waiting.append(p)

    def mark_dead(self, patient_id: str):
        """Call this if a treated patient dies on the table."""
        for p in self.treated:
            if p['id'] == patient_id:
                self.treated.remove(p)
                self.dead.append(p)
                return

    def get_all_names(self) -> list:
        """Returns all patient names seen this game — used for ending screen."""
        return [p['name'] for p in self.all_patients]

    def get_summary(self) -> dict:
        """Full end-of-game summary for ending detector."""
        return {
            "treated": self.treated,
            "dead": self.dead,
            "waiting": self.waiting,
            "all": self.all_patients
        }