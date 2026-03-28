"""
Body hotspot definitions and condition-to-region mapping.
Shared data between BodyTargetingPhase and main orchestrator.
"""

# ── Condition → body region mapping ──────────────────────────────────────
# Keys are lowercase substrings — first match wins.
CONDITION_REGION_MAP = {
    # CHEST / CARDIAC
    "heart":        "chest",
    "cardiac":      "chest",
    "coronary":     "chest",
    "myocard":      "chest",
    "haemorrhage":  "chest",
    "aorta":        "chest",
    "pericardial":  "chest",
    # LUNG / RESPIRATORY
    "lung":         "chest",
    "pulmonar":     "chest",
    "pneumo":       "chest",
    "asthma":       "chest",
    "bronch":       "chest",
    "pleural":      "chest",
    # ABDOMEN
    "bowel":        "abdomen",
    "appendix":     "abdomen",
    "liver":        "abdomen",
    "stomach":      "abdomen",
    "abdom":        "abdomen",
    "spleen":       "abdomen",
    "hernia":       "abdomen",
    "perforat":     "abdomen",
    "gallbladder":  "abdomen",
    "pancreati":    "abdomen",
    # HEAD / BRAIN
    "brain":        "head",
    "cranial":      "head",
    "skull":        "head",
    "cerebr":       "head",
    "neural":       "head",
    "head":         "head",
    "dental":       "head",
    "jaw":          "head",
    "eye":          "head",
    "ear":          "head",
    # SPINE / BACK
    "spine":        "spine",
    "spinal":       "spine",
    "vertebr":      "spine",
    "disc":         "spine",
    "back":         "spine",
    # PELVIS / LOWER
    "pelvi":        "pelvis",
    "hip":          "pelvis",
    "bladder":      "pelvis",
    "kidney":       "pelvis",
    "renal":        "pelvis",
    "uterus":       "pelvis",
    "ovari":        "pelvis",
    # ARM / SHOULDER
    "shoulder":     "arm",
    "arm":          "arm",
    "elbow":        "arm",
    "wrist":        "arm",
    "hand":         "arm",
    # LEG
    "leg":          "leg",
    "knee":         "leg",
    "ankle":        "leg",
    "femur":        "leg",
    "tibia":        "leg",
    "hip fracture": "leg",
}

DEFAULT_REGION = "chest"


def condition_to_region(condition: str) -> str:
    """Map a patient's condition string to a body region key."""
    c = condition.lower()
    for keyword, region in CONDITION_REGION_MAP.items():
        if keyword in c:
            return region
    return DEFAULT_REGION


# ── Body hotspot definitions ──────────────────────────────────────────────
# Each entry: (region_key, label, rel_cx, rel_cy, rx, ry)
# rel_cx / rel_cy are fractions of the body figure's bounding box.
# rx, ry are ellipse radii in pixels.
BODY_HOTSPOTS = [
    ("head",    "HEAD",    0.50, 0.07,  38,  38),
    ("chest",   "CHEST",   0.50, 0.28,  55,  45),
    ("abdomen", "ABDOMEN", 0.50, 0.46,  48,  38),
    ("pelvis",  "PELVIS",  0.50, 0.60,  42,  28),
    ("arm",     "ARM",     0.22, 0.32,  22,  50),
    ("spine",   "SPINE",   0.50, 0.38,  14,  55),
    ("leg",     "LEG",     0.38, 0.78,  20,  55),
]