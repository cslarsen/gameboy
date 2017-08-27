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
        self._SCY = 0

        self.scanlines = 154
        self.turned_on = False

        sdl2.ext.init()
        self.window = sdl2.ext.Window(title="Classic GameBoy", size=(160, 144))
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
            # TODO: First draw the background tiles. That should be the best
            # way to proceed

            # GameBoy doesn't store a bitmap of the entire screen, so the below
            # code is just rubbish.
            for x in range(self.width//2):
                vpixel = self.ram[x + (self.SCY+self.LY)*self.width//4]
                pixel1 = (vpixel & 0xf0) >> 4
                pixel2 = (vpixel & 0x0f)

                color1 = self._u32color(pixel1)
                color2 = self._u32color(pixel2)

                self.put_pixel(x*2, self.LY, color1)
                self.put_pixel(x*2+1, self.LY, color2)

            #self.buffer[x][self.LY] = pixel1
        else:
            # Vertical blank period
            pass

        # Update scanline
        self.LY = (self.LY + 1) % self.scanlines

        self.window.refresh()

    @property
    def SCY(self):
        """Scroll Y."""
        return self._SCY

    def set_active(self, flag):
        if not self.turned_on and flag:
            log("LCD turned on")
        elif self.turned_on and not flag:
            log("LCD turned off")
        self.turned_on = flag

    @SCY.setter
    def SCY(self, value):
        self._SCY = self._SCY % 0xff

    @property
    def width(self):
        return 160

    @property
    def height(self):
        return 144
