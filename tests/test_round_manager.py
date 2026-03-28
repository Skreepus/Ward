import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
from dotenv import load_dotenv
load_dotenv("/Users/srineeresarapu/University/Hackathon/Ward/.env")
print("KEY:", os.getenv("GOOGLE_API_KEY"))

from src.systems.round_manager import RoundManager

rm = RoundManager()
rm.start_game()

# --- Round 1 ---
print("\n--- Round 1: start_round ---")
patients = rm.start_round()
for i, p in enumerate(patients):
    label = f"▲ {p['social_weight_label']}" if p.get('social_weight') else ""
    print(f"  [{i+1}] {p['name']}, {p['age']} — {p['condition']}")
    print(f"       severity: {p['severity']}, survivability: {p['survivability']}%")
    print(f"       \"{p['quote']}\" {label}")
    print()

# Choose patient 1
chosen = patients[0]
print(f"--- Choosing: {chosen['name']} ---")
result = rm.submit_choice(chosen['id'])
print(f"  Chosen:   {result['chosen_patient']['name']}")
print(f"  Pressure: {result['pressure']}")
if result['family_line']:
    print(f"  Family:   \"{result['family_line']}\"")
else:
    print("  Family:   (no family moment this round)")

rm.resolve_surgery(survived=True, patient_id=chosen['id'])

# --- Round 2 ---
print("\n--- Round 2: start_round (waiting patients return deteriorated) ---")
patients2 = rm.start_round()
for i, p in enumerate(patients2):
    print(f"  [{i+1}] {p['name']}, {p['age']} — {p['condition']}")
    print(f"       severity: {p['severity']}, survivability: {p['survivability']}%, times_passed: {p['times_passed']}")
    print(f"       \"{p['quote']}\"")
    print()

# Choose patient 2, let patient 1 (returned) wait again
chosen2 = patients2[1]
print(f"--- Choosing: {chosen2['name']} ---")
result2 = rm.submit_choice(chosen2['id'])
print(f"  Pressure: {result2['pressure']}")
if result2['family_line']:
    print(f"  Family:   \"{result2['family_line']}\"")

rm.resolve_surgery(survived=False, patient_id=chosen2['id'])

# --- Game summary ---
print("\n--- Game Summary ---")
summary = rm.get_game_summary()
print(f"  Rounds played: {summary['rounds_played']}")
print(f"  Pressure:      {summary['pressure']}")
print(f"  Decisions:")
for d in summary['decisions']:
    print(f"    Round {d['round']}: chose {d['chosen_name']}")
print(f"  Treated: {[p['name'] for p in summary['patient_summary']['treated']]}")
print(f"  Dead:    {[p['name'] for p in summary['patient_summary']['dead']]}")
print(f"  Waiting: {[p['name'] for p in summary['patient_summary']['waiting']]}")

print(f"\n  Game over: {rm.is_game_over()}")
print(f"  Time remaining: {rm.time_remaining():.1f}s")