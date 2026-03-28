import pygame
import textwrap
from .config import (
    CARD_W, CARD_H, CARD_PAD, ACCENT, MUTED, OFF_WHITE,
    DANGER, CARD_BG, CARD_BORDER, CARD_SEL, CARD_SEL_BDR
)

def draw_patient_card(surf, x, y, patient, selected=False, index=1, fonts=None, hovered=False):
    """Draw an individual patient card with improved design"""
    if fonts is None:
        from .fonts import init_fonts
        fonts = init_fonts()
    
    # Determine background color based on state
    if selected:
        bg = CARD_SEL
        bdr = CARD_SEL_BDR
        border_width = 3
    elif hovered:
        bg = (28, 28, 28)
        bdr = ACCENT
        border_width = 2
    else:
        bg = CARD_BG
        bdr = CARD_BORDER
        border_width = 1

    pygame.draw.rect(surf, bg, (x, y, CARD_W, CARD_H))
    pygame.draw.rect(surf, bdr, (x, y, CARD_W, CARD_H), border_width)

    cx = x + CARD_PAD
    cy = y + CARD_PAD

    # Key number - larger
    num_col = ACCENT if selected else MUTED
    num = fonts['xlarge'].render(f"[{index}]", True, num_col)
    surf.blit(num, (cx, cy))

    # Returning patient indicator
    if patient.get("returning"):
        ret = fonts['small'].render("← RETURNING", True, DANGER)
        surf.blit(ret, (x + CARD_W - ret.get_width() - CARD_PAD, cy + 5))

    cy += 38

    # Name + age - larger, more prominent
    name_surf = fonts['title'].render(f"{patient['name']}, {patient['age']}", True, OFF_WHITE)
    surf.blit(name_surf, (cx, cy))
    cy += 30

    # Condition - medium size, muted color
    cond_surf = fonts['medium'].render(patient["condition"], True, MUTED)
    surf.blit(cond_surf, (cx, cy))
    cy += 28

    # Divider
    pygame.draw.line(surf, CARD_BORDER, (cx, cy), (x + CARD_W - CARD_PAD, cy), 1)
    cy += 12

    # Severity label
    sev_label = fonts['severity'].render("SEVERITY", True, MUTED)
    surf.blit(sev_label, (cx, cy))
    cy += 18

    # 5-BAR SEVERITY
    severity = patient["severity"]
    severity_5 = max(1, min(5, (severity + 1) // 2))
    
    severity_colors = {
        1: (255, 255, 150),   # Light Yellow
        2: (255, 200, 100),   # Orange-Yellow  
        3: (255, 150, 50),    # Orange
        4: (220, 80, 40),     # Dark Orange-Red
        5: (160, 30, 30),     # Deep Red
    }
    
    bar_color = severity_colors[severity_5]
    
    bar_width = 50
    bar_height = 10
    bar_gap = 8
    
    for i in range(5):
        if i < severity_5:
            col = bar_color
        else:
            col = (40, 40, 40)
        pygame.draw.rect(surf, col, (cx + i * (bar_width + bar_gap), cy, bar_width, bar_height))
    
    cy += 22

    # Survivability - SMALLER TEXT, NO COLOR
    pct = patient["survivability"]
    pct_surf = fonts['percent'].render(f"{pct}% survival with treatment", True, MUTED)
    surf.blit(pct_surf, (cx, cy))
    cy += 28

    # Quote - FIXED TEXT WRAPPING with wider width
    quote = f'"{patient["quote"]}"'
    # Increased wrap width to 45 characters to prevent orphaned words
    wrapped = textwrap.wrap(quote, width=45)
    for line in wrapped[:2]:
        q_surf = fonts['small'].render(line, True, (185, 185, 155))
        surf.blit(q_surf, (cx, cy))
        cy += 18

    # Social flag
    flag_text = None
    if patient.get("flag") == "donor":
        flag_text = "▲ HOSPITAL DONOR"
    elif patient.get("social_weight") and patient.get("social_weight_label"):
        flag_text = patient.get("social_weight_label")
    
    if flag_text:
        flag_surf = fonts['small'].render(flag_text, True, (180, 150, 80))
        surf.blit(flag_surf, (cx, y + CARD_H - CARD_PAD - 18))