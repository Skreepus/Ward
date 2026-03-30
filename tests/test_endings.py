import os, sys
from dotenv import load_dotenv
load_dotenv("/Users/srineeresarapu/University/Hackathon/Ward/.env")
sys.path.insert(0, "/Users/srineeresarapu/University/Hackathon/Ward")

from src.systems.outcome_manager import OutcomeTracker
from src.systems.ending_detector import EndingDetector

# ── Mock patients ──────────────────────────────────────────────────────────
high   = {"id":"p1","name":"Ruth Calloway","survivability":88,"severity":6,"social_weight":False,"times_passed":0,"quote":"","had_family_present":False,"condition":"Bowel perforation"}
donor  = {"id":"p2","name":"Daniel Marsh","survivability":72,"severity":7,"social_weight":True,"times_passed":0,"quote":"","had_family_present":True,"condition":"Ruptured appendix"}
quiet  = {"id":"p3","name":"Priya Nair","survivability":61,"severity":8,"social_weight":False,"times_passed":2,"quote":"","had_family_present":False,"condition":"Internal haemorrhage"}
low    = {"id":"p4","name":"George Mills","survivability":30,"severity":9,"social_weight":False,"times_passed":3,"quote":"","had_family_present":False,"condition":"Aortic dissection"}

def run(label, records, pressure, dead_ids=[], waiting=[]):
    tracker = OutcomeTracker()
    for r in records:
        tracker.record(**r)

    all_patients = [high, donor, quiet, low]
    dead = [p for p in all_patients if p["id"] in dead_ids]

    summary = {
        "all":     all_patients,
        "treated": [p for p in all_patients if p["id"] not in dead_ids and p["id"] not in [w["id"] for w in waiting]],
        "dead":    dead,
        "waiting": waiting,
    }

    detector = EndingDetector(tracker, pressure, summary, total_deaths=len(dead))
    ending   = detector.detect()
    print(f"\n{'='*40}")
    print(f"SCENARIO: {label}")
    print(f"ENDING:   {ending['title']}")
    print(f"SUBTITLE: {ending['subtitle']}")
    print(f"BODY:\n{ending['body']}")
    if ending.get("context"):
        print(f"CONTEXT:  {ending['context']}")

# ── Scenarios ──────────────────────────────────────────────────────────────

run("Clinical Perfection",
    records=[
        dict(round_number=1, chosen_patient=high, passed_patients=[donor, quiet], survived=True,  minigame_failed=False),
        dict(round_number=2, chosen_patient=donor, passed_patients=[quiet, low],  survived=True,  minigame_failed=False),
        dict(round_number=3, chosen_patient=high, passed_patients=[quiet],        survived=True,  minigame_failed=False),
    ],
    pressure=0, dead_ids=["p4"])

run("Promoted",
    records=[
        dict(round_number=1, chosen_patient=donor, passed_patients=[high, quiet], survived=True, minigame_failed=False),
        dict(round_number=2, chosen_patient=donor, passed_patients=[quiet, low],  survived=True, minigame_failed=False),
    ],
    pressure=4)

run("The Quiet Ones",
    records=[
        dict(round_number=1, chosen_patient=high,  passed_patients=[quiet, low],  survived=True, minigame_failed=False),
        dict(round_number=2, chosen_patient=donor, passed_patients=[quiet],        survived=True, minigame_failed=False),
    ],
    pressure=0)

run("Still On The List",
    records=[
        dict(round_number=1, chosen_patient=high,  passed_patients=[donor, quiet], survived=True, minigame_failed=False),
        dict(round_number=2, chosen_patient=donor, passed_patients=[low],           survived=True, minigame_failed=False),
    ],
    pressure=0, waiting=[quiet])

run("Ghosts",
    records=[
        dict(round_number=1, chosen_patient=high, passed_patients=[donor, quiet, low], survived=False, minigame_failed=True),
        dict(round_number=2, chosen_patient=high, passed_patients=[quiet, low],         survived=False, minigame_failed=True),
    ],
    pressure=0, dead_ids=["p1","p2","p3","p4","p4"])

run("The Complaint",
    records=[
        dict(round_number=1, chosen_patient=high, passed_patients=[donor], survived=True, minigame_failed=True),
        dict(round_number=2, chosen_patient=high, passed_patients=[donor], survived=True, minigame_failed=True),
        dict(round_number=3, chosen_patient=high, passed_patients=[donor], survived=True, minigame_failed=True),
    ],
    pressure=2)