import os
import json
from dotenv import load_dotenv
load_dotenv("/Users/srineeresarapu/University/Hackathon/Ward/.env")
print("KEY:", os.getenv("GOOGLE_API_KEY"))

from src.systems.patient_generator import PatientGenerator

pg = PatientGenerator()

# Round 1 — get fresh patients
print("\n--- Round 1: get_round_patients ---")
round1 = pg.get_round_patients(round_number=1)
for p in round1:
    print(f"  [{p['id']}] {p['name']}, {p['age']} — {p['condition']} (survivability: {p['survivability']}%)")
    print(f"  \"{p['quote']}\"")
    print()

# Pick the first patient to treat
chosen = round1[0]
print(f"--- Treating: {chosen['name']} ---")
pg.resolve_round(treated_id=chosen['id'], round_patients=round1)

print(f"\nTreated: {[p['name'] for p in pg.treated]}")
print(f"Waiting: {[p['name'] for p in pg.waiting]}")
print(f"Dead:    {[p['name'] for p in pg.dead]}")

# Round 2 — waiting patients should come back deteriorated
print("\n--- Round 2: get_round_patients (deteriorated patients return) ---")
round2 = pg.get_round_patients(round_number=2)
for p in round2:
    print(f"  [{p['id']}] {p['name']} — severity: {p['severity']}, survivability: {p['survivability']}%, times_passed: {p['times_passed']}")
    print(f"  \"{p['quote']}\"")
    print()

# End of game summary
print("--- Game Summary ---")
summary = pg.get_summary()
print(json.dumps({
    "treated": [p['name'] for p in summary['treated']],
    "dead":    [p['name'] for p in summary['dead']],
    "waiting": [p['name'] for p in summary['waiting']],
}, indent=2))