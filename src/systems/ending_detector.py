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
}


class EndingDetector:
    def __init__(self, outcome_tracker, pressure: int, patient_summary: dict):
        """
        outcome_tracker: OutcomeTracker instance
        pressure: int from RoundManager
        patient_summary: dict from PatientGenerator.get_summary()
        """
        self.tracker = outcome_tracker
        self.pressure = pressure
        self.patient_summary = patient_summary
        self.summary = outcome_tracker.summary()

    def detect(self) -> dict:
        """
        Returns the ending dict with id, title, subtitle, body,
        and extra context (patient list, dead while waiting, etc).
        """
        ending_id = self._pick_ending()
        ending = ENDINGS[ending_id].copy()

        # Attach context for the ending screen to render
        ending["context"] = self._build_context(ending_id)
        return ending

    def _pick_ending(self) -> str:
        """
        Priority order:
        1. Promoted  — high pressure (social weight abuse)
        2. Clinical Perfection — always picked by survivability
        3. The Quiet Ones — ignored patients with no voice
        4. Fired — default / everything else
        """
        if self.tracker.total_pressure(self.pressure):
            return "promoted"

        if self.summary["always_clinical"]:
            return "clinical_perfection"

        if self.summary["ignored_quiet"]:
            return "the_quiet_ones"

        return "fired"

    def _build_context(self, ending_id: str) -> dict:
        all_patients = self.patient_summary.get("all", [])
        all_dead     = self.patient_summary.get("dead", [])

        if ending_id == "clinical_perfection":
            # Show the one patient who died waiting despite correct decisions
            died_waiting = self.tracker.get_dead_while_waiting(all_dead)
            return {
                "died_waiting": died_waiting[0] if died_waiting else None
            }

        if ending_id == "the_quiet_ones":
            # Show names of quiet patients who were passed over
            quiet = self.tracker.get_passed_no_family(all_patients)
            return {
                "quiet_patients": quiet
            }

        if ending_id == "promoted":
            # Show full patient list with one line each, no outcomes
            return {
                "patient_list": [
                    {"name": p["name"], "condition": p["condition"]}
                    for p in all_patients
                ]
            }

        if ending_id == "fired":
            return {}

        return {}