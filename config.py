# Screen
WIDTH, HEIGHT = 1280, 720
FPS = 60
TITLE = "WARD"

# Colours
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DIM = (160, 160, 160)
RED = (180, 40, 40)

# Timing (ms)
TYPEWRITER_SPEED = 30
MINIGAME_WINDOW = 800
ROUND_DURATION = 90          # seconds per round
TOTAL_RUNTIME = 480          # 8 minutes total

# API
import google.generativeai as genai

MODEL = "gemini-2.0-flash"
MAX_TOKENS = 1000

# Rounds
NUM_ROUNDS = 6