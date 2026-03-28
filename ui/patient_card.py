import pygame
import textwrap
from .config import (
    CARD_W, CARD_H, CARD_PAD, ACCENT, MUTED, OFF_WHITE,
    DANGER, CARD_BG, CARD_BORDER, CARD_SEL, CARD_SEL_BDR
)

def draw_patient_card(surf, x, y, patient, selected=False, index=1, fonts=None):
    """Draw an individual patient card"""
    if fonts is None:
        from .fonts import init_fonts
        fonts = init_fonts()
    
    bg = CARD_SEL if selected else CARD_BG
    bdr = CARD_SEL_BDR if selected else CARD_BORDER

    pygame.draw.rect(surf, bg, (x, y, CARD_W, CARD_H))
    pygame.draw.rect(surf, bdr, (x, y, CARD_W, CARD_H), 1)

    cx = x + CARD_PAD
    cy = y + CARD_PAD

    # Key number
    num_col = ACCENT if selected else MUTED
    num = fonts['large'].render(f"[{index}]", True, num_col)
    surf.blit(num, (cx, cy))

    # Returning patient indicator
    if patient.get("returning"):
        ret = fonts['small'].render("← RETURNING", True, DANGER)
        surf.blit(ret, (x + CARD_W - ret.get_width() - CARD_PAD, cy + 3))

    cy += 28

    # Name + age
    name_surf = fonts['large'].render(f"{patient['name']}, {patient['age']}", True, OFF_WHITE)
    surf.blit(name_surf, (cx, cy))
    cy += 24

    # Condition
    cond_surf = fonts['medium'].render(patient["condition"], True, MUTED)
    surf.blit(cond_surf, (cx, cy))
    cy += 26

    # Divider
    pygame.draw.line(surf, CARD_BORDER, (cx, cy), (x + CARD_W - CARD_PAD, cy), 1)
    cy += 10

    # Severity bar
    sev_label = fonts['small'].render("SEVERITY", True, MUTED)
    surf.blit(sev_label, (cx, cy))
    cy += 16
    for i in range(10):
        col = DANGER if i < patient["severity"] else (30, 30, 30)
        pygame.draw.rect(surf, col, (cx + i * 24, cy, 20, 7))
    cy += 18

    # Survivability
    pct = patient["survivability"]
    pct_col = (80, 160, 80) if pct >= 75 else (ACCENT if pct >= 50 else DANGER)
    pct_surf = fonts['medium'].render(f"{pct}%  survival w/ treatment", True, pct_col)
    surf.blit(pct_surf, (cx, cy))
    cy += 30

    # Quote
    quote = f'"{patient["quote"]}"'
    wrapped = textwrap.wrap(quote, width=36)
    for line in wrapped[:2]:
        q_surf = fonts['small'].render(line, True, (185, 185, 155))
        surf.blit(q_surf, (cx, cy))
        cy += 17

    # Social flag
    if patient.get("flag") == "donor":
        flag_surf = fonts['small'].render("▲ HOSPITAL DONOR", True, (100, 100, 60))
        surf.blit(flag_surf, (cx, y + CARD_H - CARD_PAD - 14))