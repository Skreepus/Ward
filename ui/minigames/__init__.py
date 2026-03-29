"""
Minigames package - contains all sub-minigames for different body parts
"""
from .base import BaseMinigame
from .ecg_minigame import ECGMinigame
from .reaction_minigame import ReactionMinigame
from .cutscene_success import SuccessCutscene
from .cutscene_failure import FailureCutscene
from .spine_minigame import SpineMinigame

__all__ = [
    'BaseMinigame', 
    'ECGMinigame', 
    'ReactionMinigame',
    'SuccessCutscene',
    'FailureCutscene'
]

