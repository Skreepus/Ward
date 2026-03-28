class Typewriter:
    """Text animation with typewriter effect"""
    
    def __init__(self, text, cps=42):
        self.full = text
        self.cps = cps
        self.elapsed = 0.0
        self.done = False

    def update(self, dt):
        if not self.done:
            self.elapsed += dt
            if self.elapsed * self.cps >= len(self.full):
                self.done = True

    def text(self):
        return self.full[:int(self.elapsed * self.cps)]

    def skip(self):
        self.elapsed = len(self.full) / self.cps
        self.done = True