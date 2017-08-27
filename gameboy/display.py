from memory import Memory
from util import make_randomized_array

class Display(object):
    def __init__(self):
        self.ram = Memory(0x2000, randomized=True, name="Display RAM")
        self.vblank_duration = 1.1
        self.fps = 59.7

        # pseudo-registers
        self.ly = 0
        self.scanlines = 154

    def step(self):
        # Actually, while drawing, we should update the current scanline
        self.ly = (self.ly + 1) % self.scanlines

    @property
    def width(self):
        return 160

    @property
    def height(self):
        return 144
