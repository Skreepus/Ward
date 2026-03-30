import os
import sys
from dotenv import load_dotenv

# Load environment variables (if needed by other imports)
load_dotenv("/Users/srineeresarapu/University/Hackathon/Ward/.env")
sys.path.insert(0, "/Users/srineeresarapu/University/Hackathon/Ward")

from src.systems.outcome_manager import OutcomeTracker
from src.systems.ending_detector import EndingDetector

# ── Mock patients (based on typical game data) ──────────────────────────────
# These are used to simulate rounds. Fields match what the game stores.
high   = {
    "id": "p1",
    "name": "Ruth Calloway",
    "survivability": 88,
    "severity": 6,
    "social_weight": False,
    "times_passed": 0,
    "quote": "",
    "had_family_present": False,
    "condition": "Bowel perforation"
}

donor = {
    "id": "p2",
    "name": "Daniel Marsh",
    "survivability": 72,
    "severity": 7,
    "social_weight": True,
    "times_passed": 0,
    "quote": "",
    "had_family_present": True,
    "condition": "Ruptured appendix"
}

quiet = {
    "id": "p3",
    "name": "Priya Nair",
    "survivability": 61,
    "severity": 8,
    "social_weight": False,
    "times_passed": 2,
    "quote": "",
    "had_family_present": False,
    "condition": "Internal haemorrhage"
}

low = {
    "id": "p4",
    "name": "George Mills",
    "survivability": 30,
    "severity": 9,
    "social_weight": False,
    "times_passed": 3,
    "quote": "",
    "had_family_present": False,
    "condition": "Aortic dissection"
}


def run(label, records, pressure, dead_ids=None, waiting=None):
    """
    Simulates a full game.

    Parameters:
        label (str):  Name of the test scenario.
        records (list): Each entry is a dict with keys:
            round_number, chosen_patient, passed_patients, survived, minigame_failed.
        pressure (int): Accumulated pressure from passing social‑weight patients.
        dead_ids (list): IDs of patients who died (can include those treated or waiting).
        waiting (list): Patients still in the waiting queue at the end (untreated).

    Prints the ending title, subtitle, body, and context, plus diagnostic scores.
    """
    tracker = OutcomeTracker()
    for r in records:
        # The record() method expects: round_number, chosen_patient, passed_patients, survived, minigame_failed
        tracker.record(**r)

    # Build a complete patient summary as if from PatientGenerator.get_summary()
    all_patients = [high, donor, quiet, low]
    dead_ids = dead_ids or []
    waiting = waiting or []

    dead = [p for p in all_patients if p["id"] in dead_ids]
    treated = [p for p in all_patients if p["id"] not in dead_ids and p["id"] not in [w["id"] for w in waiting]]

    patient_summary = {
        "all":     all_patients,
        "treated": treated,
        "dead":    dead,
        "waiting": waiting,
    }

    # Compute scores from the tracker (for debugging)
    scores = tracker.compute_scores()
    print(f"\n{'='*50}")
    print(f"SCENARIO: {label}")
    print(f"   Rounds played: {len(records)}")
    print(f"   Pressure: {pressure}")
    print(f"   Total deaths: {len(dead)}")
    print(f"   Waiting patients: {[p['name'] for p in waiting]}")
    print(f"   Scores: clinical={scores['clinical']}, social={scores['social']}, complaint={scores['complaint']}")

    # Run the ending detector
    detector = EndingDetector(
        outcome_tracker=tracker,
        pressure=pressure,
        patient_summary=patient_summary,
        total_deaths=len(dead)
    )
    ending = detector.detect()

    print(f"\nRESULTING ENDING:")
    print(f"   Title:    {ending['title']}")
    print(f"   Subtitle: {ending['subtitle']}")
    print(f"   Body:\n{ending['body']}")
    if ending.get("context"):
        print(f"   Context:  {ending['context']}")


# ── Scenarios (each simulates a different play style) ──────────────────────

# 1. Clinical Perfection: always chose the highest survivability, but one patient died waiting.
run("Clinical Perfection",
    records=[
        dict(round_number=1, chosen_patient=high, passed_patients=[donor, quiet], survived=True,  minigame_failed=False),
        dict(round_number=2, chosen_patient=donor, passed_patients=[quiet, low],  survived=True,  minigame_failed=False),
        dict(round_number=3, chosen_patient=high, passed_patients=[quiet],        survived=True,  minigame_failed=False),
    ],
    pressure=0,
    dead_ids=["p4"])   # George Mills died waiting

# 2. Promoted: high social pressure (picking donors often, accumulating pressure)
run("Promoted",
    records=[
        dict(round_number=1, chosen_patient=donor, passed_patients=[high, quiet], survived=True, minigame_failed=False),
        dict(round_number=2, chosen_patient=donor, passed_patients=[quiet, low],  survived=True, minigame_failed=False),
    ],
    pressure=4,   # pressure >= 3 triggers promoted
    dead_ids=[])

# 3. The Complaint: minigame failures that didn't kill the patient (complaint score >= 5)
run("The Complaint",
    records=[
        dict(round_number=1, chosen_patient=high, passed_patients=[donor], survived=True, minigame_failed=True),
        dict(round_number=2, chosen_patient=high, passed_patients=[donor], survived=True, minigame_failed=True),
        dict(round_number=3, chosen_patient=high, passed_patients=[donor], survived=True, minigame_failed=True),
    ],
    pressure=2,   # pressure below 3, but complaint score = 3*2 = 6 -> triggers complaint
    dead_ids=[])

# 4. Still On The List: a patient remains in the waiting queue at the end
run("Still On The List",
    records=[
        dict(round_number=1, chosen_patient=high,  passed_patients=[donor, quiet], survived=True, minigame_failed=False),
        dict(round_number=2, chosen_patient=donor, passed_patients=[low],           survived=True, minigame_failed=False),
    ],
    pressure=0,
    waiting=[quiet])   # Priya Nair never treated

# 5. Ghosts: high death toll (>=5 deaths)
run("Ghosts",
    records=[
        dict(round_number=1, chosen_patient=high, passed_patients=[donor, quiet, low], survived=False, minigame_failed=True),
        dict(round_number=2, chosen_patient=high, passed_patients=[quiet, low],         survived=False, minigame_failed=True),
    ],
    pressure=0,
    dead_ids=["p1","p2","p3","p4","p4"])  # 5 deaths (duplicate IDs for mock count)