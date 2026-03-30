import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


ENDINGS = {
    "clinical_perfection": { # nobody dies
        "id": "clinical_perfection",
        "title": "Clinical Perfection",
        "subtitle": "Your record is clean.",
        "body": (
            "Your shift has ended.\n\n"
            "The board reviewed your shift. Every decision you made was defensible.\n"
            "You followed the data. You chose the patients with the highest survivability.\n"
            "No complaints have been filed.\n\n"
            "One patient, you saw their file three times. Three times you passed them over.\n"
            "They died waiting.\n\n"
            "The hospital will not mention this in their evaluation.\n"
            "There is no protocol for regret. No box to check.\n\n"
            "You saved lives tonight. The numbers prove it.\n"
            "Yet the numbers will not tell you if you did the right thing.\n"
            "Did you do the right thing?"

        ),
    },
    "promoted": {  # helped a spesh person
        "id": "promoted",
        "title": "Promoted",
        "subtitle": "The Chief of Medicine would like to see you.",
        "body": (
            "Your shift has ended.\n\n"
            "The board has been watching your work for some time.\n"
            "You understand how this hospital functions.\n"
            "The patients with influence were treated first. You made the right people happy.\n"
            "You made the right people happy.\n"
            "You made the right people happy.\n"
            "Did you do the right thing?\n\n\n"
            "There is a position available.\n"
            "Your new office has a window.\n"
            "You will no longer see patients. You will manage the ones who do.\n\n"
            "You have been promoted, do you feel proud?"
        ),
    },
    "still_on_the_list": {    # 
        "id": "still_on_the_list",
        "title": "Still On The List",
        "subtitle": "",
        "body": (
            "Your shift has ended.\n\n"
            "There is one patient you never saw. Their name is still on the board.\n"
            "They were there when you arrived. They were there when you left.\n"
            "Their file has been passed to the next doctor.\n"
            "The next doctor will make their own choices.\n"
            "They will see the file. The one you never opened.\n\n\n"

            "In triage, someone always waits. Someone always will.\n"
            "That is not a defect. That is the design.\n"
        ),
    },
    "ghosts": {
        "id": "ghosts",
        "title": "Ghosts",
        "subtitle": "",
        "body": (
            "Your shift has ended.\n\n"
            "There were many patients at the ward tonight.\n"
            "There were many patients who didn't leave the ward tonight\n\n"
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
            "Your shift has ended.\n\n"
            "A family member has submitted a formal complaint.\n"
            "It was filed at 04:12. Twelve minutes after the surgery ended.\n\n"
            "The complaint does not concern a death. The patient survived.\n"
            "It concerns something that was said. Or not said. In the corridor.\n"
            "You remember the corridor. You remember the face.\n"
            "You do not remember the words.\n\n"
            "A doctor hardly remembers their patients\n\n"
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
        scores       = self.summary.get("scores", {})
        clinical     = scores.get("clinical",  0)
        social       = scores.get("social",    0)
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