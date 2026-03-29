import pygame
import textwrap
from .config import (
    W, H,
    NEAR_BLACK, ACCENT, MUTED, OFF_WHITE, PANEL_BORDER
)

def draw_panel(surf, rect, prompt_tw, selected, round_num, total_rounds, time_str, fonts=None, current_patients=None):
    """Draw the bottom control panel - NO PATIENT BUTTONS"""
    if fonts is None:
        from .fonts import init_fonts
        fonts = init_fonts()
    
    px, py, pw, ph = rect

    # Panel background and top border
    pygame.draw.rect(surf, NEAR_BLACK, rect)
    pygame.draw.line(surf, ACCENT, (px, py), (px + pw, py), 2)

    lx = px + 32
    ly = py + 12

    # Status line
    status = f"ROUND {round_num}/{total_rounds}   ·   {time_str}   ·   ONE THEATRE AVAILABLE"
    st_surf = fonts['panel'].render(status, True, MUTED)
    surf.blit(st_surf, (lx, ly))
    ly += 22

    # Thin divider
    pygame.draw.line(surf, PANEL_BORDER, (lx, ly), (px + pw - 32, ly), 1)
    ly += 10

    # Typewriter prompt text
    prompt_text = prompt_tw.text()
    lines = textwrap.wrap(prompt_text, width=100)
    for line in lines[:2]:
        line_surf = fonts['panel'].render(line, True, OFF_WHITE)
        surf.blit(line_surf, (lx, ly))
        ly += 22

    # Blink cursor while typewriting
    if not prompt_tw.done and lines:
        blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
        if blink_on:
            cursor = fonts['panel'].render("▌", True, ACCENT)
            last_w = fonts['panel'].size(lines[-1])[0] if lines else 0
            surf.blit(cursor, (lx + last_w, ly - 22))

    # Confirm hint - LARGER and centered
    if selected is not None:
        conf = fonts['large'].render("press ENTER to confirm", True, ACCENT)  # Changed to 'large' font
        conf_rect = conf.get_rect(center=(W//2, py + ph - 25))  # Moved up slightly
        surf.blit(conf, conf_rect)
    else:
        hint = fonts['panel'].render("CLICK ON A PATIENT CARD OR PRESS 1, 2, 3", True, MUTED)
        hint_rect = hint.get_rect(center=(W//2, py + ph - 22))
        surf.blit(hint, hint_rect)