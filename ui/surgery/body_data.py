"""
Body hotspot definitions and condition-to-region mapping.
Shared data between BodyTargetingPhase and main orchestrator.
"""

# ── Condition → body region mapping ──────────────────────────────────────
# Keys are lowercase substrings — first match wins.
CONDITION_REGION_MAP = {
    # CHEST / CARDIAC
    "coronary":     "chest",
    "myocard":      "chest",
    "aorta":        "chest",
    "pericardial":  "chest",
    "heart":        "chest",
    "cardiac":      "chest",
    "haemorrhage":  "chest",      # internal haemorrhage
    
    # LUNG / RESPIRATORY
    "lung":         "chest",
    "asthma":       "chest",
    "bronch":       "chest",
    "pneumo":       "chest",      # pneumonia
    "pleural":      "chest",      # pleural effusion
    "respiratory":  "chest",
    
    # ABDOMEN
    "bowel":        "abdomen",
    "appendix":     "abdomen",
    "liver":        "abdomen",
    "gallbladder":  "abdomen",
    "stomach":      "abdomen",
    "abdom":        "abdomen",
    "spleen":       "abdomen",
    "hernia":       "abdomen",
    "perforat":     "abdomen",
    "pancreati":    "abdomen",
    
    # HEAD / BRAIN
    "cranial":      "head",
    "epilepsy":     "head",
    "brain":        "head",
    "skull":        "head",
    "cerebr":       "head",
    "neural":       "head",
    "head":         "head",
    "dental":       "head",
    "jaw":          "head",
    "eye":          "head",
    "ear":          "head",
    "facial":       "head",
    "tooth":        "head",
    "mouth":        "head",
    
    # ARM / SHOULDER
    "shoulder":     "arm",
    "arm":          "arm",
    "elbow":        "arm",
    "wrist":        "arm",
    "hand":         "arm",
    "radius":       "arm",
    "ulna":         "arm",
    "humerus":      "arm",
    "clavicle":     "arm",
    
    # LEG
    "knee":         "leg",
    "ankle":        "leg",
    "femur":        "leg",
    "tibia":        "leg",
    "leg":          "leg",
    "hip fracture": "leg",
    "fibula":       "leg",
    "patella":      "leg",
    "foot":         "leg",
    
    # SPINE / BACK
    "spine":        "spine",
    "back":         "spine",
    "vertebr":      "spine",
    "spinal":       "spine",
    "disc":         "spine",
    "lumbar":       "spine",
    "cervical":     "spine",
    
    # PELVIS / LOWER
    "pelvi":        "pelvis",
    "hip":          "pelvis",
    "bladder":      "pelvis",
    "kidney":       "pelvis",
    "renal":        "pelvis",
    "uterus":       "pelvis",
    "ovari":        "pelvis",
    "prostate":     "pelvis",
    "pelvic":       "pelvis",
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