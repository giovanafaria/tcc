from enum import Enum

class MobilityType(Enum):
    """
    Enhanced mobility type system for agents with properties
    """
    NON_PWD = ("blue", 1.0)
    MOTOR = ("orange", 0.55) # weighted average from three studies (wheelchair, amputed and amputed with crutches)
    VISUAL = ("red", 0.4)  # average: Bennett et al., 2019
    INTELLECTUAL = ("purple", 0.65)  # Oppewal et al., 2018

    def __init__(self, color, speed):
        self.color = color
        self.speed = speed

    @property
    def value(self):
        return (self.color, self.speed)