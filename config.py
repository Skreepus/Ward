import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

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
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
MODEL = "gemini-2.0-flash"
MAX_TOKENS = 1000

# Rounds
NUM_ROUNDS = 6
```

Also add `python-dotenv` to your requirements:
```
pygame==2.6.1
google-generativeai>=0.8.0
python-dotenv>=1.0.0
```

And make sure your `.gitignore` has:
```
.env
venv/
__pycache__/
*.pyc