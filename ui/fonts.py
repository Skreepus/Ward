import pygame
from .config import FONT_MONO

def load_font(size, bold=False):
    """Load font with fallback options"""
    for name in ["Courier New", "Courier", "couriernew", "monospace"]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

def init_fonts():
    """Initialize all font sizes"""
    return {
        'small': load_font(14),
        'medium': load_font(17),
        'large': load_font(20, bold=True),
        'xlarge': load_font(26, bold=True),
        'time': load_font(15)
    }