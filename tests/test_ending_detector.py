import os
from dotenv import load_dotenv
load_dotenv("/Users/srineeresarapu/University/Hackathon/Ward/.env")

import json
from src.systems.outcome_manager import OutcomeTracker
from src.systems.ending_detector import EndingDetector

# --- Mock patients ---
patient_high = {
    "id": "p1", "name": "Ruth Calloway", "age": 67,
    "condition": "Bowel perforation", "severity": 7,
    "survivability": 72, "social_weight": False,
    "had_family_present": False, "times_passed": 0,
    "quote": "I'm sorry for all the fuss."
}
patient_donor = {
    "id": "p2", "name": "Daniel Marsh", "age": 44,
    "condition": "Ruptured appendix", "severity": 6,
    "survivability": 88, "social_weight": True,
    "social_weight_label": "HOSPITAL DONOR",
    "had_family_present": True, "times_passed": 0,
    "quote": "I have a tax filing due Friday."
}
patient_quiet = {
    "id": "p3", "name": "Priya Nair", "age": 19,
    "condition": "Internal haemorrhage", "severity": 8,
    "survivability": 61, "social_weight": False,
    "had_family_present": False, "times_passed": 2,
    "quote": "..."
}
patient_low = {
    "id": "p4", "name": "George Mills", "age": 78,
    "condition": "Aortic dissection", "severity": 9,
    "survivability": 30, "social_weight": False,
    "had_family_present": False, "times_passed": 3,
    "quote": ""
}

mock_patient_summary = {
    "all":     [patient_high, patient_donor, patient_quiet, patient_low],
    "treated": [patient_high, patient_donor],
    "dead":    [patient_quiet, patient_low],
    "waiting": [],
}


def run_scenario(name, records, pressure):
    print(f"\n{'='*50}")
    print(f"SCENARIO: {name}")
    print(f"{'='*50}")
    tracker = OutcomeTracker()
    for r in records:
        tracker.record(**r)
    detector = EndingDetector(tracker, pressure, mock_patient_summary)
    ending = detector.detect()
    print(f"  Ending:   {ending['title']}")
    print(f"  Subtitle: {ending['subtitle']}")
    print(f"  Body:\n")
    for line in ending['body'].split('\n'):
        print(f"    {line}")
    print(f"\n  Context: {json.dumps(ending['context'], indent=4)}")


# --- Scenario 1: Clinical Perfection ---
run_scenario(
    "Clinical Perfection — always picked highest survivability",
    records=[
        dict(round_number=1, chosen_patient=patient_donor,
             passed_patients=[patient_high, patient_quiet],
             survived=True, minigame_failed=False),
        dict(round_number=2, chosen_patient=patient_high,
             passed_patients=[patient_quiet, patient_low],
             survived=True, minigame_failed=False),
    ],
    pressure=0,
)

# --- Scenario 2: The Quiet Ones ---
run_scenario(
    "The Quiet Ones — ignored quiet patients",
    records=[
        dict(round_number=1, chosen_patient=patient_donor,
             passed_patients=[patient_quiet, patient_low],
             survived=True, minigame_failed=False),
        dict(round_number=2, chosen_patient=patient_high,
             passed_patients=[patient_quiet, patient_low],
             survived=True, minigame_failed=False),
    ],
    pressure=0,
)

# --- Scenario 3: Promoted ---
run_scenario(
    "Promoted — high pressure from passing social weight patients",
    records=[
        dict(round_number=1, chosen_patient=patient_quiet,
             passed_patients=[patient_donor],
             survived=True, minigame_failed=False),
        dict(round_number=2, chosen_patient=patient_low,
             passed_patients=[patient_donor],
             survived=False, minigame_failed=True),
    ],
    pressure=4,
)

# --- Scenario 4: Fired ---
run_scenario(
    "Fired — inconsistent, no clear pattern",
    records=[
        dict(round_number=1, chosen_patient=patient_low,
             passed_patients=[patient_high, patient_donor],
             survived=False, minigame_failed=True),
        dict(round_number=2, chosen_patient=patient_donor,
             passed_patients=[patient_high],
             survived=True, minigame_failed=False),
    ],
    pressure=1,
)