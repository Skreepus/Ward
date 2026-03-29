"""
Minigames package - contains all sub-minigames for different body parts
"""
from .base import BaseMinigame
from .ecg_minigame import ECGMinigame
from .reaction_minigame import ReactionMinigame
from .spine_minigame import SpineMinigame
from .arm_minigame import ArmMinigame
from .leg_minigame import LegMinigame
from .pelvis_minigame import PelvisMinigame
from .brain_puzzle_minigame import BrainPuzzleMinigame


__all__ = [
    'BaseMinigame', 
    'ECGMinigame', 
    'ReactionMinigame',
    'SuccessCutscene',
    'FailureCutscene'
]

