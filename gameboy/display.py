from memory import Memory
from util import make_randomized_array

class Display(object):
    def __init__(self):
        self.ram = Memory(0x2000, randomized=True, name="Display RAM")
        self.vblank_duration = 1.1
        self.fps = 59.7

        # pseudo-registers
        self.LY = 0
        self._SCY = 0

        self.scanlines = 154

    def step(self):
        # Actually, while drawing, we should update the current scanline
        self.LY = (self.LY + 1) % self.scanlines

    @property
    def SCY(self):
        """Scroll Y."""
        return self._SCY

    @SCY.setter
    def SCY(self, value):
        self._SCY = self._SCY % 0xff

    @property
    def width(self):
        return 160

    @property
    def height(self):
        return 144
