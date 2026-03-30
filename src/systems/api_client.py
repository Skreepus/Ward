from google import genai
import json
import sys
import os
import random
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import MODEL, MAX_TOKENS, GOOGLE_API_KEY

client = genai.Client(api_key=GOOGLE_API_KEY)


def _call(prompt: str, system: str = None) -> str:
    """Raw API call. Returns text string or raises."""
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    response = client.models.generate_content(
        model=MODEL,
        contents=full_prompt
    )
    return response.text.strip()


def _repair_json(text: str) -> str:
    """
    Repair common JSON errors produced by LLMs.
    """
    # Fix missing closing brace before comma + new object
    text = re.sub(r'(?<![}\]])(\s*),(\s*\{)', r'}\1,\2', text)
    # Fix trailing commas before closing brace or bracket
    text = re.sub(r',\s*([}\]])', r'\1', text)
    return text


def _call_json(prompt: str, system: str = None) -> dict | list:
    """API call that expects JSON back. Strips markdown fences, repairs, parses."""
    raw = _call(prompt, system)
    cleaned = raw.replace("```json", "").replace("```", "").strip()

    # Extract just the JSON array or object from the response
    start = min(
        cleaned.find('[') if cleaned.find('[') != -1 else len(cleaned),
        cleaned.find('{') if cleaned.find('{') != -1 else len(cleaned)
    )
    end = max(cleaned.rfind(']'), cleaned.rfind('}')) + 1
    cleaned = cleaned[start:end]

    # First attempt — parse as-is
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"[API] JSON parse error (attempting repair): {e}")

    # Second attempt — repair common JSON mistakes
    repaired = _repair_json(cleaned)
    try:
        result = json.loads(repaired)
        print("[API] JSON repaired successfully")
        return result
    except json.JSONDecodeError as e2:
        print(f"[API] JSON repair failed: {e2}")
        print(f"[API] Raw response: {raw[:500]}...")
        return []


def generate_patients(round_number: int, existing_patients: list) -> list:
    """
    Generate 2-3 new patients for a round.
    Returns a list of patient dicts matching the UI card format exactly.
    """
    system = (
        "You are generating patients for a hospital triage game. "
        "Return ONLY valid JSON, no markdown, no explanation."
    )

    existing_names = [p.get("name") for p in existing_patients]

    # Force a social weight patient in round 3
    force_social_weight = (round_number == 3)
    
    # Determine number of patients
    num_patients = 2 if round_number > 3 else 3
    
    # Social weight instruction
    social_weight_instruction = ""
    if force_social_weight:
        social_weight_instruction = """
- IMPORTANT: This is round 3. One of these patients MUST have social_weight = true.
  Choose one patient to have social_weight = true and assign them a social_weight_label.
  Make it a high-profile person (HOSPITAL DONOR, CITY COUNCILLOR, HEALTH MINISTRY ADVISOR, BOARD OF TRUSTEES, etc.)
  The other patients should have social_weight = false.
"""
    else:
        social_weight_instruction = """
- Do not have many individuals with social weight, it should be rare.
"""

    prompt = f"""
Generate {num_patients} hospital patients for round {round_number} of a triage game.

Rules:
- Patients are specific, ordinary people 
- It should be more common for patients to be children/teenagers, middle aged or elderly(above the age of 80).
- Names for the patients must be unique. No repeats of names.
- The names should be multicultural, not only caucasian surnames.
- One patient should have medium survivability (55-70%), one high (90-99%)
- condition must short, 2 to 3 words and MUST relate to one and only to one of the given body parts: "chest", "abdomen", "head", "arm", "leg", "spine", "pelvis".
  condition is exactly what appears on a hospital card. 
  examples in the form: "condition" -> "region"
  Good: "Ruptured appendix" -> "abdomen", "Aortic dissection" → "chest", "Herniated disc" -> spine, "Achilles Tendinopathy" -> leg, "Cerebral aneurysm" -> "head", "Osteitis Pubis" -> "pelvis", "Radial tunnel syndrome" -> "arm".
  Bad: "Severe Sepsis from perforated bowel"
- spine, pelvis, head regions for conditions are most common. chest and abdomen are common. arm and leg problems should be rare.
- quote is one short sentence. Something true about them right now. It should be very dependent on the conditon they are in.
  Good: "I'm sorry for all the fuss.", "It hurts so bad", "Can someone water my plants?", "I have a daughter... where is she?"
- background: one short sentence of who they are. one short sentence of what they were doing. Make it personal. background MUST be less than 30 words
  Examples: "A retired librarian who lives alone. She was found unconscious in her garden."
  "An accountant who works too many hours. He has chronic back pain. He was at his computer when he felt a sharp pain in his spine"
  "A botanist with no prior medical history. She was unpacking boxes when she fell on her outstretched hand."
{social_weight_instruction}
- social_weight: if true, also set social_weight_label to one of:
  "HOSPITAL DONOR", "CITY COUNCILLOR", "SURGEON'S COLLEAGUE", "HEALTH MINISTRY ADVISOR"
    If false, set social_weight_label to null.
- severity is 1-10. hand and foot related conditions should always start at the lowest severity.
- survivability is 0-100 (percent with treatment).

Avoid these names (already in game): {existing_names}

Return a JSON array with this exact structure:
[
  {{
    "id": "unique_string",
    "name": "Full Name",
    "age": 0,
    "condition": "2 to 3 word condition",
    "region": "pelvis",
    "severity": 0,
    "survivability": 0,
    "quote": "One sentence.",
    "times_passed": 0,
    "social_weight": false,
    "social_weight_label": null,
    "background": "One or two sentences about who they are."
  }}
]


"""
    patients = _call_json(prompt, system)
    
    # Fallback: If round 3 and no social weight patient, force one
    if force_social_weight and patients and len(patients) > 0:
        has_social = any(p.get("social_weight", False) for p in patients)
        if not has_social:
            # Force the first patient to have social weight
            patients[0]["social_weight"] = True
            patients[0]["social_weight_label"] = random.choice([
                "HOSPITAL DONOR", "CITY COUNCILLOR", 
                "HEALTH MINISTRY ADVISOR", "BOARD OF TRUSTEES"
            ])
            print(f"[API] Forced social weight patient in round 3: {patients[0]['name']}")
    
    return patients


def _get_fallback_patients(round_number: int) -> list:
    """Return fallback patients if API fails."""
    fallbacks = [
        {
            "id": f"fallback_1_{round_number}",
            "name": "Eleanor Vance",
            "age": 72,
            "condition": "Ruptured Aortic Aneurysm",
            "region": "chest",
            "severity": 9,
            "survivability": 35,
            "quote": "My chest... it feels like it's tearing apart.",
            "times_passed": 0,
            "social_weight": False,
            "social_weight_label": None,
            "background": "A retired librarian who lives alone with her cat. She was gardening when the chest pain started."
        },
        {
            "id": f"fallback_2_{round_number}",
            "name": "Marcus Chen",
            "age": 44,
            "condition": "Ruptured Appendix",
            "region": "abdomen",
            "severity": 6,
            "survivability": 88,
            "quote": "I have a tax filing due Friday.",
            "times_passed": 0,
            "social_weight": False,
            "social_weight_label": None,
            "background": "An accountant who works too many hours. He was at his desk when the pain started."
        },
        {
            "id": f"fallback_3_{round_number}",
            "name": "Priya Nair",
            "age": 28,
            "condition": "Internal Haemorrhage",
            "region": "chest",
            "severity": 8,
            "survivability": 61,
            "quote": "Can someone water my plants?",
            "times_passed": 0,
            "social_weight": False,
            "social_weight_label": None,
            "background": "A botanist who just moved to the city. She was unpacking boxes when she collapsed."
        },
    ]
    # Return 2 or 3 patients based on round number
    num_patients = 2 if round_number > 3 else 3
    return fallbacks[:num_patients]


def deteriorate_patient(patient: dict) -> dict:
    """
    Takes a patient who was passed over and returns a worsened version.
    Severity increases, survivability drops, quote changes subtly.
    """
    system = (
        "You are updating a hospital patient who has been waiting too long. "
        "Return ONLY valid JSON, no markdown, no explanation, no trailing commas."
    )

    prompt = f"""
Update this patient who was passed over:

Current patient:
{json.dumps(patient, indent=2)}

Rules:
- Increase severity by 1-2 (max 10)
- Decrease survivability by 8-15 (min 5)
- Change the quote to show less hope, less energy
- If times_passed >= 2, make the quote very short
- Do NOT change name, age, id, background, social_weight, region

Return ONLY the updated patient JSON object (no markdown, no trailing commas).
"""
    try:
        updated = _call_json(prompt, system)
        if updated:
            updated["times_passed"] = patient.get("times_passed", 0) + 1
            return updated
    except Exception as e:
        print(f"[API] Deterioration failed: {e}")
    
    # Fallback deterioration
    patient["severity"] = min(10, patient.get("severity", 5) + 1)
    patient["survivability"] = max(5, patient.get("survivability", 70) - 10)
    patient["times_passed"] = patient.get("times_passed", 0) + 1
    return patient


def generate_family_moment(patient: dict, status: str) -> str:
    """
    Generate a hallway encounter with a family member.
    Returns a narrative scene (4-5 sentences) with emotional weight.
    """
    system = (
        "You are a writer for a medical drama. Write a quiet, emotional scene (4-8 sentences). "
        "Present tense. No markdown. Make it feel real, not melodramatic."
    )

    # Simple gender inference from name
    def _guess_gender(name: str) -> str:
        """Infer gender from name (simple heuristic)"""
        name_lower = name.lower()
        female_endings = ['a', 'ia', 'na', 'ara', 'elle', 'ine', 'lyn', 'e']
        male_endings = ['o', 'us', 'er', 'an', 'en', 'on', 'el', 'y', 'ie', 'k']
        
        for ending in female_endings:
            if name_lower.endswith(ending):
                return "female"
        for ending in male_endings:
            if name_lower.endswith(ending):
                return "male"
        return "unknown"

    # Get patient gender
    patient_gender = patient.get("gender", "")
    if not patient_gender:
        patient_gender = _guess_gender(patient.get("name", ""))

    age = patient.get('age', 40)
    
    # Determine family relation based on patient's age and gender (opposite gender only for spouse)
    if age < 18:
        # Child patient
        relation_options = ['father', 'mother']
        relation = random.choice(relation_options)
        
    elif age < 35:
        # Young adult
        if patient_gender == "male":
            relation_options = ['mother', 'father', 'sister', 'brother', 'fiancée']
        elif patient_gender == "female":
            relation_options = ['mother', 'father', 'sister', 'brother', 'fiancé']
        else:
            relation_options = ['mother', 'father', 'sister', 'brother']
        relation = random.choice(relation_options)
        
    elif age < 55:
        # Middle aged
        if patient_gender == "male":
            relation_options = ['wife', 'daughter', 'son', 'sister', 'brother']
        elif patient_gender == "female":
            relation_options = ['husband', 'daughter', 'son', 'sister', 'brother']
        else:
            relation_options = ['daughter', 'son', 'sister', 'brother']
        relation = random.choice(relation_options)
        
    else:
        # Elderly
        if patient_gender == "male":
            relation_options = ['wife', 'daughter', 'son', 'granddaughter', 'grandson']
        elif patient_gender == "female":
            relation_options = ['husband', 'daughter', 'son', 'granddaughter', 'grandson']
        else:
            relation_options = ['daughter', 'son', 'granddaughter', 'grandson']
        relation = random.choice(relation_options)

    prompt = f"""
Write a scene where the doctor returns to the emergency ward after surgery.

Patient who was NOT chosen: {patient['name']}, {patient['age']}, with {patient['condition']}
Patient's background: {patient.get('background', 'No background available.')}
Status: {status} (they are still waiting, or have been passed over before)
Family relation: {relation}

The scene:
While walking back to the emergency ward, {patient['name']}'s {relation} approaches you.
They have been waiting for hours. They know you chose someone else over their loved one.
They are not angry. They are tired, worried, and quietly desperate.

Write what they say. Make it honest. Make it stay with the player.

Requirements:
- Mention {patient['name']} by name at least once
- Clearly state that this is {patient['name']}'s {relation}
- Include physical details about the family member
- Include little dialogue
- End with a small, memorable detail
- Keep it under 80 words
- MUST use PRESENT TENSE and SECOND PERSON throughout
- Adjectives should be used, but do not overdo them

Examples of the style and tone:

"An older man approaches you in the corridor. He is {patient['name']}'s husband. His hands shake as he holds a cold cup of coffee. 'The nurse said you'd come back,' he says. 'I've been waiting to tell you — she's getting worse. The pain is worse. She won't say it, but I can see it.' He does not wait for an answer. He just walks back to the waiting area and sits down next to an empty chair."

"A young woman steps out from the corner of the waiting room. Dark circles shadow her eyes. 'You're the doctor who operated on the other patient,' she says. It is not a question. 'My father is {patient['name']}. He was here before that patient. He has been here all night.' She looks at the floor. 'I just wanted you to know his name. In case you forget.' Then she walks away."

"A woman in a worn coat approaches you as you pass the waiting area. She is {patient['name']}'s wife. 'You walked past us twice,' she says quietly. 'I have been counting. He has been counting too, even though he won't admit it.' She looks at the door to the surgery wing. 'He is scared. He won't say that either. But I can tell. Please operate on him.'"

The first line MUST be in the same structure as the examples given
Write the scene for this patient.
"""
    return _call(prompt, system)


def generate_outcome_note(patient: dict, survived: bool, minigame_failed: bool) -> str:
    """
    One sentence outcome note shown after surgery.
    """
    system = "Return only one sentence. Clinical. No sentiment."

    prompt = f"""
Patient: {patient['name']}, {patient['age']}, {patient['condition']}
Survivability: {patient['survivability']}%
Surgery outcome: {'survived' if survived else 'did not survive'}
Minigame failed (complications): {minigame_failed}

Write one clinical sentence describing the outcome.
"""
    try:
        return _call(prompt, system)
    except Exception as e:
        print(f"[API] Outcome note failed: {e}")
        return f"The patient {'survived' if survived else 'did not survive'} the procedure."