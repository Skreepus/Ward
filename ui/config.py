import os


# Game settings
NUM_ROUNDS = 6
ROUND_DURATION = 45  # seconds per round
TOTAL_RUNTIME = 300  # 5 minutes total game time
MODEL = "gemini-2.0-flash-exp"  # Gemini model
MAX_TOKENS = 1024

# Google API Key (you'll need to set this as an environment variable)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Constants and configuration
W, H = 1280, 720
PANEL_H = int(H * 0.27)
IMG_H = H - PANEL_H
FPS = 60

# Colors
BLACK = (0, 0, 0)
NEAR_BLACK = (8, 8, 8)
OFF_WHITE = (210, 210, 205)
MUTED = (120, 120, 115)
ACCENT = (148, 148, 72)
DANGER = (175, 38, 38)
DIM_OVERLAY = (0, 0, 0, 140)

PANEL_BORDER = (38, 38, 38)
CARD_BG = (14, 14, 14)
CARD_BORDER = (48, 48, 48)
CARD_SEL = (38, 38, 22)
CARD_SEL_BDR = (148, 148, 72)

# Card dimensions
CARD_W = 340
CARD_H = 250
CARD_PAD = 16

# Font names
FONT_MONO = "couriernew"