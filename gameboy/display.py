import sdl2
import sdl2.ext
import sys

from memory import Memory
from util import (
    dot,
    log,
)

class DummyDisplay(object):
    """A display in case you don't want one or can have one.

    E.g. you're on PyPy and don't have SDL, or you're just debugging.
    """
    def __init__(self, title):
        self.width = 256
        self.height = 256

    def pump_events(self):
        pass

    def put(self, x, y, color):
        pass

    def update(self):
        pass

    def clear(self, color):
        pass

class HostDisplay(object):
    """The actual display shown on the computer screen."""
    def __init__(self, title):
        self.width = 256
        self.height = 256

        sdl2.ext.init()

        self.window = sdl2.ext.Window(title=title, size=(self.width,
            self.height))
        self.window.show()

        # TODO: Only display 160x144 pixels, but have a back buffer with
        # 256x256
        self.buffer = sdl2.ext.pixels2d(self.window.get_surface())

    def pump_events(self):
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                raise StopIteration("SDL quit")

    def put(self, x, y, color):
        self.buffer[x][y] = color

    def update(self):
        self.window.refresh()

    def clear(self, color):
        for y in range(self.height):
            for x in range(self.width):
                self.put(x, y, color)

class Display(object):
    """The GameBoy display system."""
    def __init__(self, no_display=False):
        self.ram = Memory(0x2000, offset=0x8000, randomized=True,
                name="Display RAM")

        self.vblank_duration = 1.1
        self.fps = 59.7

        # pseudo-registers
        self.LY = 0
        self.SCY = 0
        self.SCX = 0
        self.BGPAL = 0
        self._LCDCONT = 0

        self.scanlines = 154
        self.turned_on = False

        # Actual display area
        self.vwidth = 256
        self.vheight = 256

        # Shown area
        self.width = 160
        self.height = 144

        self.window = DummyDisplay("GameBoy")
        self._setup_host_display(no_display)

        self.palette = {
            0: 0xffffff,
            1: 0xaaaaaa,
            2: 0x555555,
            3: 0x000000,
        }

    def _setup_host_display(self, no_display):
        if no_display:
            return

        try:
            import numpy # required by SDL2
        except ImportError as e:
            log("Disabling display, needs numpy: %s" % e)
            return

        try:
            self.window = self.window = HostDisplay("GameBoy")
        except Exception as e:
            log("Cannot open host display: %s" % e)

        self.window.clear(0x008855)

    def palette_to_rgb(self, color):
        """Converts GameBoy palette color to a 24-bit RGB value."""
        color_for_bugs = 0xff0000
        return self.palette.get(color, color_for_bugs)

    def put_pixel(self, x, y, color):
        assert(color < 4)
        self.window.put(x, y, self.palette_to_rgb(color))

    def inc_ly(self):
        self.LY = (self.LY + 1) % self.scanlines

    def step(self):
        self.window.pump_events()

        # If the display is turned off, just exit
        if self.lcd_operation:
            self.read_palette()

            if self.LY < self.height:
                if self.background_display:
                    self.render_background()
            else:
                # Vertical blank period
                pass
            self.inc_ly()

        self.window.update()

    def read_palette(self):
        colors = {
            0: 0xffffff, # lightest
            1: 0xaaaaaa,
            2: 0x555555,
            3: 0x000000, # darkest
        }

        col3 = (self.BGPAL & 0b11000000) >> 6
        col2 = (self.BGPAL & 0b00110000) >> 4
        col1 = (self.BGPAL & 0b00001100) >> 2
        col0 = (self.BGPAL & 0b00000011) >> 0

        self.palette[0] = colors[col0]
        self.palette[1] = colors[col1]
        self.palette[2] = colors[col2]
        self.palette[3] = colors[col3]

    def render_background(self):
        # Read the tile table
        bitmap_addr, bitmap_addr_end = self.tile_table_address

        xpos, ypos = 0, 0
        for index in range(32*32):
            # TODO: Find out if its signed or unsigned mode and adjust
            # starting address based on that
            tile_number = self.ram[0x8000 - self.ram.offset + index]

            # Get the tile bitmap; 8x8 pixels stored as 2-bit colors
            # meaning 16 bytes of memory
            bitmap = []
            line = []
            tile_data_start, tile_data_end = self.tile_data_address
            for n in range(16):
                byte = self.ram[tile_data_start - self.ram.offset + n]
                pix1 = (byte & 0b11000000) >> 6
                pix2 = (byte & 0b00110000) >> 4
                pix3 = (byte & 0b00001100) >> 2
                pix4 = (byte & 0b00000011) >> 0
                line += [pix1, pix2, pix3, pix4]
                # TODO: Use BGPAL
                if len(line) == 8:
                    bitmap.append(line)
                    line = []

            # Draw bitmap on virtual display
            for y in range(len(bitmap)):
                line = bitmap[y]
                for x in range(len(line)):
                    color = line[x]
                    self.put_pixel(x + xpos, y + ypos, color)
            xpos += 8
            if xpos == self.window.width:
                xpos = 0
                ypos += 8
                if ypos == self.window.height:
                    break

    @property
    def LCDCONT(self):
        return self._LCDCONT

    @LCDCONT.setter
    def LCDCONT(self, value):
        self._LCDCONT = value % 0xff
        log("LCDCONT display=%s background=%s" % ("on" if self.lcd_operation
            else "off", "on" if self.background_display else "off"))

    @property
    def lcd_operation(self):
        return (self._LCDCONT & (1<<7)) !=0

    @property
    def tile_data_address(self):
        if (self._LCDCONT & (1<<4)) == 0:
            return 0x9800, 0x9bff
        else:
            return 0x9c00, 0x9fff

    @property
    def tile_table_address(self):
        if (self._LCDCONT & (1<<4)) == 0:
            return 0x8800, 0x97ff
        else:
            return 0x8000, 0x8fff

    @property
    def background_display(self):
        return (self._LCDCONT & 1) == 1
