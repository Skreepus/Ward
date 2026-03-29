import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

ENDINGS = {
    "clinical_perfection": {
        "id": "clinical_perfection",
        "title": "Clinical Perfection",
        "subtitle": "Your record is clean.",
        "body": (
            "Every decision you made was defensible.\n"
            "The numbers support you.\n"
            "The board has reviewed your shift.\n"
            "No complaints have been filed.\n\n"
            "There is one patient you saw several times.\n"
            "Low survivability. Correctly passed over each time.\n"
            "They died waiting.\n\n"
            "Nothing about your decisions was incorrect."
        ),
    },
    "the_quiet_ones": {
        "id": "the_quiet_ones",
        "title": "The Quiet Ones",
        "subtitle": "The hospital considers your record exemplary.",
        "body": (
            "You responded well under pressure.\n"
            "Your patients were engaged. Present. Vocal.\n\n"
            "Below are the names of patients who said little.\n"
            "Who had no one waiting for them.\n"
            "Who were passed over.\n\n"
            "Most are gone."
        ),
    },
    "promoted": {
        "id": "promoted",
        "title": "Promoted",
        "subtitle": "The Chief of Medicine would like to see you.",
        "body": (
            "The board has been watching your work.\n"
            "You understand how this hospital functions.\n"
            "There is a position available.\n\n"
            "Your new office has a window.\n"
            "You will no longer see patients.\n\n"
            "None of the patients from your last shift\n"
            "were part of the promotion decision."
        ),
    },
    "fired": {
        "id": "fired",
        "title": "Fired.",
        "subtitle": "",
        "body": (
            "You have been removed from the roster.\n\n"
            "The reasons are not disputed.\n"
            "There will be no appeal."
        ),
    },
    "ghosts": {
        "id": "ghosts",
        "title": "Ghosts of the Ward",
        "subtitle": "The dead are not silent.",
        "body": (
            "Too many have died on your shift.\n"
            "Their names echo in the corridors.\n\n"
            "The hospital will not speak of it.\n"
            "But you will carry them with you."
        ),
    },
}


class EndingDetector:
    def __init__(self, outcome_tracker, pressure: int, patient_summary: dict, total_deaths: int = 0, family_moments: int = 0):
        """
        outcome_tracker: OutcomeTracker instance
        pressure: int from RoundManager
        patient_summary: dict from PatientGenerator.get_summary()
        total_deaths: total number of patients who died (waiting or after surgery)
        family_moments: number of family overlays shown
        """
        self.tracker = outcome_tracker
        self.pressure = pressure
        self.patient_summary = patient_summary
        self.total_deaths = total_deaths
        self.family_moments = family_moments
        self.summary = outcome_tracker.summary()

    def detect(self) -> dict:
        ending_id = self._pick_ending()
        ending = ENDINGS[ending_id].copy()
        ending["context"] = self._build_context(ending_id)
        return ending

    def _pick_ending(self) -> str:
        # High death toll → Ghosts
        if self.total_deaths >= 4:
            return "ghosts"
        # Promoted by pressure
        if self.tracker.total_pressure(self.pressure):
            return "promoted"
        # Clinical perfection
        if self.summary["always_clinical"]:
            return "clinical_perfection"
        # Ignored quiet ones
        if self.summary["ignored_quiet"]:
            return "the_quiet_ones"
        # Default fired
        return "fired"

    def _build_context(self, ending_id: str) -> dict:
        all_patients = self.patient_summary.get("all", [])
        all_dead     = self.patient_summary.get("dead", [])

        if ending_id == "clinical_perfection":
            died_waiting = self.tracker.get_dead_while_waiting(all_dead)
            return {
                "died_waiting": died_waiting[0] if died_waiting else None
            }
        if ending_id == "the_quiet_ones":
            quiet = self.tracker.get_passed_no_family(all_patients)
            return {"quiet_patients": quiet}
        if ending_id == "promoted":
            return {
                "patient_list": [
                    {"name": p["name"], "condition": p["condition"]}
                    for p in all_patients
                ]
            }
        if ending_id == "ghosts":
            return {"dead_names": [p["name"] for p in all_dead]}
        return {}