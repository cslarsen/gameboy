from memory import Memory
from util import make_randomized_array

class Display(object):
    def __init__(self):
        self.ram = Memory(0x2000, randomized=True)
        self.vblank_duration = 1.1
        self.fps = 59.7

    @property
    def width(self):
        return 160

    @property
    def height(self):
        return 144
