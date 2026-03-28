from src.systems.api_client import (
    generate_patients,
    deteriorate_patient,
    generate_family_moment,
    generate_outcome_note
)

# 1. Generate patients for round 1
print("--- generate_patients ---")
patients = generate_patients(round_number=1, existing_patients=[])
for p in patients:
    print(p)

# 2. Deteriorate the first patient
print("\n--- deteriorate_patient ---")
worse = deteriorate_patient(patients[0])
print(worse)

# 3. Family moment
print("\n--- generate_family_moment ---")
line = generate_family_moment(patients[0], status="waiting")
print(line)

# 4. Outcome note
print("\n--- generate_outcome_note ---")
note = generate_outcome_note(patients[0], survived=True, minigame_failed=False)
print(note)