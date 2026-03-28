import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


class OutcomeTracker:
    def __init__(self):
        self.records = []   # one entry per round

    def record(
        self,
        round_number: int,
        chosen_patient: dict,
        passed_patients: list,
        survived: bool,
        minigame_failed: bool,
    ):
        """
        Call this after each round resolves.
        Stores everything the ending detector needs.
        """
        self.records.append({
            "round": round_number,

            # Who was treated
            "chosen_id":           chosen_patient["id"],
            "chosen_name":         chosen_patient["name"],
            "chosen_survivability": chosen_patient["survivability"],
            "chosen_severity":     chosen_patient["severity"],
            "chosen_social_weight": chosen_patient.get("social_weight", False),
            "chosen_had_family":   chosen_patient.get("had_family_present", False),
            "survived":            survived,
            "minigame_failed":     minigame_failed,

            # Who was passed over
            "passed": [
                {
                    "id":           p["id"],
                    "name":         p["name"],
                    "survivability": p["survivability"],
                    "severity":     p["severity"],
                    "social_weight": p.get("social_weight", False),
                    "times_passed": p.get("times_passed", 0),
                    "quote":        p.get("quote", ""),
                }
                for p in passed_patients
            ],
        })

    # ------------------------------------------------------------------
    # Pattern analysis — used by ending_detector
    # ------------------------------------------------------------------

    def always_picked_highest_survivability(self) -> bool:
        """True if every choice was the highest survivability patient."""
        for r in self.records:
            all_survivabilities = [p["survivability"] for p in r["passed"]]
            all_survivabilities.append(r["chosen_survivability"])
            if r["chosen_survivability"] < max(all_survivabilities):
                return False
        return True

    def mostly_picked_social_weight(self) -> bool:
        """True if >50% of chosen patients had social weight."""
        if not self.records:
            return False
        social_picks = sum(1 for r in self.records if r["chosen_social_weight"])
        return social_picks / len(self.records) > 0.5

    def ignored_quiet_patients(self) -> bool:
        """
        True if the player consistently passed over patients
        who had no family present and low social weight.
        """
        quiet_passed = 0
        total_passed = 0
        for r in self.records:
            for p in r["passed"]:
                total_passed += 1
                if not p["social_weight"] and p["times_passed"] >= 1:
                    quiet_passed += 1
        if total_passed == 0:
            return False
        return quiet_passed / total_passed > 0.5

    def total_pressure(self, pressure: int) -> bool:
        """True if pressure accumulated enough to trigger the promotion ending."""
        return pressure >= 3

    def get_dead_while_waiting(self, all_dead: list) -> list:
        """
        Returns patients who died waiting (never treated).
        Used for the Clinical Perfection ending screen.
        """
        treated_ids = {r["chosen_id"] for r in self.records}
        return [p for p in all_dead if p["id"] not in treated_ids]

    def get_passed_no_family(self, all_patients: list) -> list:
        """
        Returns patients who were passed over, had no social weight,
        and no family present. Used for The Quiet Ones ending screen.
        """
        return [
            p for p in all_patients
            if not p.get("social_weight", False)
            and not p.get("had_family_present", False)
            and p.get("times_passed", 0) >= 1
        ]

    def summary(self) -> dict:
        """Full record dump for ending_detector."""
        return {
            "records": self.records,
            "total_rounds": len(self.records),
            "always_clinical":      self.always_picked_highest_survivability(),
            "mostly_social":        self.mostly_picked_social_weight(),
            "ignored_quiet":        self.ignored_quiet_patients(),
        }