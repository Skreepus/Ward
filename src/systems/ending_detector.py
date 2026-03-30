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
            "No complaints have been filed.\n\n"
            "There is one patient you saw several times.\n"
            "They died waiting.\n\n"
            "Nothing about your decisions was incorrect."
        ),
    },
    "the_quiet_ones": {
        "id": "the_quiet_ones",
        "title": "The Quiet Ones",
        "subtitle": "The hospital considers your record exemplary.",
        "body": (
            "You finished your shift.\n"
            "The patients you treated were grateful.\n\n"
            "Some patients are not listed in your outcomes.\n"
            "They are listed below.\n\n"
            "They did not make a fuss."
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
    "still_on_the_list": {
        "id": "still_on_the_list",
        "title": "Still On The List",
        "subtitle": "",
        "body": (
            "Your shift has ended.\n\n"
            "One patient was never seen.\n"
            "They are still in the system.\n"
            "Their file has been passed to the next doctor.\n\n"
            "They were on the list when you arrived.\n"
            "They are on the list now."
        ),
    },
    "ghosts": {
        "id": "ghosts",
        "title": "Ghosts",
        "subtitle": "",
        "body": (
            "Too many patients did not leave this ward tonight.\n\n"
            "The hospital will not speak of it publicly.\n"
            "There will be a review.\n"
            "You will be asked to provide notes.\n\n"
            "The names are below."
        ),
    },
    "the_complaint": {
        "id": "the_complaint",
        "title": "The Complaint",
        "subtitle": "A formal complaint has been filed.",
        "body": (
            "A family member has submitted a complaint.\n"
            "It was filed at 04:12.\n\n"
            "The complaint does not concern a death.\n"
            "It concerns something that was said,\n"
            "or not said, in the corridor.\n\n"
            "HR has been notified.\n"
            "You will receive a letter."
        ),
    },
}


class EndingDetector:
    def __init__(self, outcome_tracker, pressure: int, patient_summary: dict,
                 total_deaths: int = 0):
        """
        outcome_tracker:  OutcomeTracker instance
        pressure:         int from RoundManager
        patient_summary:  dict from PatientGenerator.get_summary()
        total_deaths:     total number of dead patients
        """
        self.tracker         = outcome_tracker
        self.pressure        = pressure
        self.patient_summary = patient_summary
        self.total_deaths    = total_deaths
        self.summary         = outcome_tracker.summary()

    def detect(self) -> dict:
        ending_id        = self._pick_ending()
        ending           = ENDINGS[ending_id].copy()
        ending["context"] = self._build_context(ending_id)
        return ending

    def _pick_ending(self) -> str:
        # Use scores computed by the tracker
        scores       = self.summary.get("scores", {})
        clinical     = scores.get("clinical",  0)
        social       = scores.get("social",    0)
        quiet        = scores.get("quiet",     0)
        complaint    = scores.get("complaint", 0)

        all_patients = self.patient_summary.get("all",     [])
        waiting      = self.patient_summary.get("waiting", [])

        # Ghosts — hard threshold on deaths
        if self.total_deaths >= 5:
            return "ghosts"

        # Promoted — social pressure dominates
        if self.pressure >= 3 or social >= 6:
            return "promoted"

        # The Complaint — minigame failures + family pressure
        if complaint >= 5:
            return "the_complaint"

        # Clinical Perfection — consistently picked by survivability
        if clinical >= 4 and social < 3:
            return "clinical_perfection"

        # The Quiet Ones — consistently ignored quiet patients
        if quiet >= 4:
            return "the_quiet_ones"

        # Still On The List — someone is still waiting at end of shift
        if waiting:
            return "still_on_the_list"

        # Default
        return "still_on_the_list"

    def _build_context(self, ending_id: str) -> dict:
        all_patients = self.patient_summary.get("all",     [])
        all_dead     = self.patient_summary.get("dead",    [])
        waiting      = self.patient_summary.get("waiting", [])

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

        if ending_id == "still_on_the_list":
            patient = waiting[0] if waiting else None
            return {"waiting_patient": patient}

        if ending_id == "ghosts":
            return {
                "dead_names": [p["name"] for p in all_dead]
            }

        if ending_id == "the_complaint":
            return {}

        return {}