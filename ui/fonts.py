import pygame
from .config import FONT_MONO

def load_font(size, bold=False, italic=False):
    """Load font with fallback options"""
    for name in ["Courier New", "Courier", "couriernew", "monospace"]:
        try:
            return pygame.font.SysFont(name, size, bold=bold, italic=italic)
        except Exception:
            pass
    return pygame.font.Font(None, size)

def init_fonts():
    """Initialize all font sizes"""
    return {
        'small': load_font(14),
        'medium': load_font(18),
        'large': load_font(26, bold=True),    # Larger for confirm text
        'xlarge': load_font(28, bold=True),
        'time': load_font(16),
        'title': load_font(24, bold=True),
        'severity': load_font(12),
        'percent': load_font(16),
        'panel': load_font(16),
        'hint': load_font(14),
        'confirm': load_font(32, bold=True),  # New - very large for confirm text
    }