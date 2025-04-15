from enum import Enum

class MobilityType(Enum):
    """
    Enhanced mobility type system for agents with properties
    """
    NON_PWD = ("blue", 1.0)
    WHEELCHAIR = ("orange", 0.5)
    BLIND = ("red", 0.4)
    CRUTCHES = ("purple", 0.6)
    
    def __init__(self, color, speed):
        self.color = color
        self.speed = speed

    @property
    def value(self):
        return (self.color, self.speed)