import pygame
import textwrap
from .config import (
    NEAR_BLACK, ACCENT, MUTED, OFF_WHITE, PANEL_BORDER
)

def draw_panel(surf, rect, prompt_tw, selected, round_num, total_rounds, time_str, fonts=None):
    """Draw the bottom control panel"""
    if fonts is None:
        from .fonts import init_fonts
        fonts = init_fonts()
    
    px, py, pw, ph = rect

    # Panel background and top border
    pygame.draw.rect(surf, NEAR_BLACK, rect)
    pygame.draw.line(surf, ACCENT, (px, py), (px + pw, py), 1)

    lx = px + 32
    ly = py + 16

    # Status line
    status = f"ROUND {round_num}/{total_rounds}   ·   {time_str}   ·   ONE THEATRE AVAILABLE"
    st_surf = fonts['time'].render(status, True, MUTED)
    surf.blit(st_surf, (lx, ly))
    ly += 22

    # Thin divider
    pygame.draw.line(surf, PANEL_BORDER, (lx, ly), (px + pw - 32, ly), 1)
    ly += 12

    # Typewriter prompt text
    prompt_text = prompt_tw.text()
    lines = textwrap.wrap(prompt_text, width=90)
    for line in lines[:3]:
        line_surf = fonts['medium'].render(line, True, OFF_WHITE)
        surf.blit(line_surf, (lx, ly))
        ly += 22

    # Blink cursor while typewriting
    if not prompt_tw.done:
        blink_on = (pygame.time.get_ticks() // 500) % 2 == 0
        if blink_on:
            cursor = fonts['medium'].render("▌", True, ACCENT)
            last_w = fonts['medium'].size(lines[-1])[0] if lines else 0
            surf.blit(cursor, (lx + last_w, ly - 22))

    # Action buttons
    by = py + ph - 44
    bx = lx
    
    from .data.patients import PATIENTS
    
    for idx, patient in enumerate(PATIENTS[:3]):
        is_sel = (selected == idx)
        b_col = ACCENT if is_sel else PANEL_BORDER
        bw = 160
        pygame.draw.rect(surf, b_col, (bx, by, bw, 28))
        
        label = f"[{idx+1}] {patient['name'].split()[0]}"
        t_col = NEAR_BLACK if is_sel else OFF_WHITE
        b_surf = fonts['medium'].render(label, True, t_col)
        surf.blit(b_surf, (bx + 10, by + 6))
        bx += bw + 12

    # Confirm hint
    if selected is not None:
        conf = fonts['small'].render("ENTER  —  confirm", True, ACCENT)
        surf.blit(conf, (bx + 8, by + 8))