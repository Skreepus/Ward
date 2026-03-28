import os
import json
from dotenv import load_dotenv
load_dotenv("/Users/srineeresarapu/University/Hackathon/Ward/.env")
print("KEY:", os.getenv("GOOGLE_API_KEY"))

from src.systems.api_client import (
    generate_patients,
    deteriorate_patient,
    generate_family_moment,
    generate_outcome_note
)

# 1. Generate patients for round 1
print("\n--- generate_patients ---")
patients = generate_patients(round_number=1, existing_patients=[])
for p in patients:
    print(json.dumps(p, indent=2))

# 2. Deteriorate the first patient
print("\n--- deteriorate_patient ---")
worse = deteriorate_patient(patients[0])
print(json.dumps(worse, indent=2))

# 3. Family moment
print("\n--- generate_family_moment ---")
line = generate_family_moment(patients[0], status="waiting")
print(f'"{line}"')

# 4. Outcome note
print("\n--- generate_outcome_note ---")
note = generate_outcome_note(patients[0], survived=True, minigame_failed=False)
print(f'"{note}"')