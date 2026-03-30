# WARD

A hospital triage game where you decide which patient gets the only available surgery theatre.  
Made for [Hackathon Name].

## How to Run

1. **Clone the repository**
   ```bash
   git clone https://github.com/Skreepus/Ward
   cd ward

2. **Create and activate a virtual environment**
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

3. **Install dependencies**
pip install -r requirements.txt

4. **Set up your API key**
copy .env.example to .env
open .env and add your Google API key. Get one from Google AI Studio

5. **Run the game**
python run.py
or 
python -m ui.main
**Controls**
1, 2, 3 – select a patient card

ENTER – confirm selection and start surgery

SPACE – skip typewriter text / dismiss overlays

ESC – return to title screen during game

**Gameplay**
Each round you are presented with 2‑3 patients. Choose one to operate on; the others will wait and their condition may worsen. After surgery, a minigame tests your skill. Family moments may appear. After 6 rounds, an ending is determined by your choices (Clinical Perfection, Promoted, The Complaint, Still On The List, or Ghosts).

**Credits**
Created by Srineer Esarapu and Kenneth Wu for Hackiethon 2026.
Uses Pygame and Google Generative AI.