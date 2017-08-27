import sdl2
import sdl2.ext
import numpy as np

from memory import Memory
from util import (
    log,
    make_randomized_array,
)

class Display(object):
    def __init__(self):
        self.ram = Memory(0x2000, randomized=True, name="Display RAM")
        self.vblank_duration = 1.1
        self.fps = 59.7

        # pseudo-registers
        self.LY = 0
        self.SCY = 0
        self.SCX = 0
        self._LCDCONT = 0

        self.scanlines = 154
        self.turned_on = False

        self.width = 160
        self.height = 144

        sdl2.ext.init()
        self.window = sdl2.ext.Window(title="Classic GameBoy",
                size=(self.width, self.height))
        self.window.show()

        self.buffer = sdl2.ext.pixels2d(self.window.get_surface())

    def _u32color(self, color):
        """Converts GameBoy colors to 24-bit colors."""
        if color == 0:
            return 0xffffff
        if color == 1:
            return 0xaaaaaa
        if color == 2:
            return 0x666666
        if color == 3:
            return 0x000000
        return 0xff0000 # Mark invalid pixels as red
        #raise RuntimeError("Invalid 4-bit color value %d" % color)

    def put_pixel(self, x, y, color):
        self.buffer[x][y] = self._u32color(color)

    def step(self):
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                raise StopIteration("SDL quit")

        if self.LY < self.height:
            # Draw background tiles
            # TODO: Read the LCDCONT register to determine whether we should
            # read from 0x8000-0x8fff or 0x8800-0x97ff.

            log("scx=%d scy=%d ly=%d lcdcont=%0.2x" % (self.SCX, self.SCY,
                self.LY, self.LCDCONT))
            for x in range(self.width//2):
                vpixel = self.ram[x + (self.SCX//2) + (self.SCY+self.LY)*self.width//4]
                pixel1 = (vpixel & 0xf0) >> 4
                pixel2 = (vpixel & 0x0f)

                color1 = self._u32color(pixel1)
                color2 = self._u32color(pixel2)

                self.put_pixel(x*2, self.LY, color1)
                self.put_pixel(x*2+1, self.LY, color2)
        else:
            # Vertical blank period
            pass

        # Update scanline
        self.LY = (self.LY + 1) % self.scanlines

        self.window.refresh()

    @property
    def LCDCONT(self):
        return self._LCDCONT

    @LCDCONT.setter
    def LCDCONT(self, value):
        self._LCDCONT = value % 0xff
        self.set_active(self._LCDCONT & (1<<7) != 0)

    def set_active(self, flag):
        if not self.turned_on and flag:
            log("LCD turned on")
        elif self.turned_on and not flag:
            log("LCD turned off")
        self.turned_on = flag
