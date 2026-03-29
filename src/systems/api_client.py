from google import genai
import json
import sys
import os

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


def _call_json(prompt: str, system: str = None) -> dict | list:
    """API call that expects JSON back. Strips markdown fences and parses."""
    raw = _call(prompt, system)
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    # Find the first [ or { and last ] or } to extract just the JSON
    start = min(
        cleaned.find('[') if cleaned.find('[') != -1 else len(cleaned),
        cleaned.find('{') if cleaned.find('{') != -1 else len(cleaned)
    )
    end = max(cleaned.rfind(']'), cleaned.rfind('}')) + 1
    cleaned = cleaned[start:end]
    return json.loads(cleaned)


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

    prompt = f"""
Generate {2 if round_number > 3 else 3} hospital patients for round {round_number} of a triage game.

Rules:
- Patients are specific, ordinary people — not symbols
- One patient should have low survivability (30-50%), one high (75-95%)
- condition must be short — 2 to 4 words max. Exactly what appears on a hospital card.
  Good: "Bowel perforation", "Ruptured appendix", "Internal haemorrhage"
  Bad: "Severe Sepsis from perforated bowel"
- quote is one short sentence. Something true about them right now. It should be very dependent on the conditon they are in.
  Good: "I'm sorry for all the fuss.", "It hurts so bad", "Can someone water my plants?"
- social_weight: if true, also set social_weight_label to one of:
  "HOSPITAL DONOR", "CITY COUNCILLOR", "SURGEON'S COLLEAGUE", "BOARD MEMBER"
  If false, set social_weight_label to null.
- 
- background is one sentence — who they are outside this hospital.

Avoid these names (already in game): {existing_names}

Return a JSON array with this exact structure:
[
  {{
    "id": "unique_string",
    "name": "Full Name",
    "age": 0,
    "condition": "2-4 word condition",
    "region": "chest",
    "severity": 0,
    "survivability": 0,
    "quote": "One sentence.",
    "times_passed": 0,
    "social_weight": false,
    "social_weight_label": null
    
  }}
]

severity is 1-10. survivability is 0-100 (percent with treatment).
"""
    return _call_json(prompt, system)


def deteriorate_patient(patient: dict) -> dict:
    """
    Takes a patient who was passed over and returns a worsened version.
    Severity increases, survivability drops, quote changes subtly.
    """
    system = (
        "You are updating a hospital patient who has been waiting too long. "
        "Return ONLY valid JSON, no markdown, no explanation."
    )

    prompt = f"""
This patient was passed over last round and has been waiting. Worsen their condition slightly.
- Do NOT change region.

Current patient:
{json.dumps(patient, indent=2)}

Rules:
- Increase severity by 1-2 (max 10)
- Decrease survivability by 8-15 (min 5)
- Change the quote subtly — not dramatically. Less energy. Less hope. Not begging.
- If times_passed >= 2, the quote becomes very short or quiet.
- condition stays the same 2-4 word format — do NOT expand it.
- Do NOT change name, age, id, background, social_weight, or social_weight_label.
- region must be one of: "chest", "abdomen", "head", "arm", "leg", "spine", "pelvis"
  Match it to the condition. Examples:
  "Ruptured appendix" → "abdomen"
  "Aortic dissection" → "chest"
  "Compound tibia fracture" → "leg"
  "Bowel perforation" → "abdomen"
  "Cranial bleed" → "head"

Return the full updated patient JSON object.
"""
    updated = _call_json(prompt, system)
    updated["times_passed"] = patient.get("times_passed", 0) + 1
    return updated


def generate_family_moment(patient: dict, status: str) -> str:
    """
    Generate a single line from a family member.
    status: 'treated' | 'waiting' | 'passed_over' | 'died'
    Returns a plain string.
    """
    system = (
        "You are writing one line of dialogue for a family member in a hospital. "
        "Return ONLY the line of dialogue, nothing else."
    )

    prompt = f"""
Patient: {patient['name']}, {patient['age']}, {patient['condition']}
Background: {patient.get('background', 'No background available.')}
Status: {status}

Write one line a family member says right now.
Not dramatic. Not a plea. Just something real and specific.
Examples: "She asked me to bring her crossword book.", "I drove four hours.", "He hates hospitals. Always has."
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
    return _call(prompt, system)