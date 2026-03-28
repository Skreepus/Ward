"""
Base class for all sub-minigames.
"""

class BaseMinigame:
    """Base class that all minigames should inherit from"""

    def __init__(self, screen, fonts, patient, region=None):
        self.screen = screen
        self.fonts = fonts
        self.patient = patient
        self.region = region
        self.result = None

    def run(self):
        """Override this method with the minigame logic"""
        raise NotImplementedError("Minigames must implement run()")