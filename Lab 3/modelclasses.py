from LightStrip import *

class FeedbackStats:
    def __init__(self):
        self._score = 100  # Start at 100
        self._lightstrip = LightStrip(pin=2, numleds=8)

    def getPercentage(self):
        return self._score / 100.0

    def showStats(self):
        numleds = int(8 * self.getPercentage())

        if numleds > 5:
            self._lightstrip.setColor(GREEN, numleds)
        elif numleds > 3:
            self._lightstrip.setColor(YELLOW, numleds)
        else:
            self._lightstrip.setColor(RED, numleds)

    def happy(self):
        self._score = min(100, self._score + 10)
        self.showStats()

    def sad(self):
        self._score = max(0, self._score - 10)
        self.showStats()

    def reset(self):
        self._score = 100 # Reset the score to 100
        self.showStats()