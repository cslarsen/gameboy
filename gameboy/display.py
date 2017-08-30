import sdl2
import sdl2.ext
import sdl2.ext.draw
import time

from memory import Memory
from util import (
    dot,
    log,
    u8_to_signed,
)

class HostDisplay(object):
    """The actual display shown on the computer screen."""
    def __init__(self, title, zoom=1):
        self.width = 256
        self.height = 256

        sdl2.ext.init()

        self.window = sdl2.ext.Window(title=title, size=(self.width*zoom,
            self.height*zoom))

        # Use SDL2 hardware acceleration
        self.renderer = sdl2.ext.Renderer(self.window,
                logical_size=(self.width, self.height),
                flags = sdl2.SDL_RENDERER_ACCELERATED |
                        sdl2.SDL_RENDERER_PRESENTVSYNC)

    def pump_events(self):
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                raise StopIteration("SDL quit")

    def put(self, x, y, color):
        self.renderer.draw_point((x,y), color)

    def line(self, color, x1, y1, x2, y2):
        self.renderer.draw_line((x1, y1, x2, y2), color)

    def show(self):
        self.window.show()

    def update(self):
        self.renderer.present()

    def clear(self, color):
        self.renderer.clear(color)

    def box(self, x, y, w, h):
        c = 0x00cc44
        self.line(c, x, y, x+w, y)
        self.line(c, x, y+h, x+w, y+h)
        self.line(c, x, y, x, y+h)
        self.line(c, x+w, y, x+w, y+h)

class Display(object):
    """The GameBoy display system."""
    def __init__(self, no_display=False, zoom=1):
        self.ram = Memory(0x2000, offset=0x8000, randomized=True,
                name="Display RAM")

        self.vblank_duration = 1.1
        self.fps = 59.7

        self.frames = 0
        self.frame_start = time.clock()

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

        self.window = HostDisplay("GameBoy", zoom=zoom)
        self.window.show()
        self.window.clear(0x474741)
        self.window.update()

        self.palette = {
            0: 0xffffff,
            1: 0xaaaaaa,
            2: 0x555555,
            3: 0x000000,
        }

    def palette_to_rgb(self, color):
        """Converts GameBoy palette color to a 24-bit RGB value."""
        color_for_bugs = 0xff0000
        return self.palette.get(color, color_for_bugs)

    def put_pixel(self, x, y, color):
        self.window.put(x, y, self.palette_to_rgb(color))

    def ly_rollover(self):
        """Increments LY and returns whether it rolled over."""
        self.LY += 1
        if self.LY == 0x100:
            self.LY = 0
            return True
        return False

    def show_viewport(self):
        """Marks viewable area"""
        self.window.box(self.SCX, self.SCY, self.width, self.height)

    def calc_fps(self):
        self.frames += 1

        now = time.clock()
        elapsed = now - self.frame_start

        if self.frames > 5 and elapsed > 2:
            fps = float(self.frames) / elapsed
            spf = 1.0 / fps
            log("%.2f fps / %.2f spf\r" % (fps, spf))
            self.frame_start = now
            self.frames = 0

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

    def render_background_scanline(self, y):
        # Read the tile table
        bitmap = self.tile_data_address - self.ram.offset
        table, signed = self.tile_table_address
        table -= self.ram.offset

        # Draw one scanline from the tiles. We do this by calculating the tile
        # index and y-position

        # For the given y line, find which tile number it is when the screen is
        # divided up in 32x32 tiles that are 8x8 pixels each.
        ypos = y & 0b11111000
        index_offset = ypos << 2

        # Position whithin this tile
        yoff = y - ypos
        bitmap += yoff*2

        handle_sign = u8_to_signed if signed else lambda x: x

        # The background consists of 32x32 tiles, so find the tile index.
        x = 0
        index = 0

        while index < 32:
            tile = handle_sign(self.ram[table + index_offset + index])

            a = self.ram[bitmap + tile*16]
            b = self.ram[bitmap + tile*16 + 1]

            p8 = ((a & 0b00000001) >> 0) | ((b & 0b00000001) << 1)
            p7 = ((a & 0b00000010) >> 1) | ((b & 0b00000010) >> 0)
            p6 = ((a & 0b00000100) >> 2) | ((b & 0b00000100) >> 1)
            p5 = ((a & 0b00001000) >> 3) | ((b & 0b00001000) >> 2)
            p4 = ((a & 0b00010000) >> 4) | ((b & 0b00010000) >> 3)
            p3 = ((a & 0b00100000) >> 5) | ((b & 0b00100000) >> 4)
            p2 = ((a & 0b01000000) >> 6) | ((b & 0b01000000) >> 5)
            p1 = ((a & 0b10000000) >> 7) | ((b & 0b10000000) >> 6)

            self.put_pixel(x+0, y, p1)
            self.put_pixel(x+1, y, p2)
            self.put_pixel(x+2, y, p3)
            self.put_pixel(x+3, y, p4)
            self.put_pixel(x+4, y, p5)
            self.put_pixel(x+5, y, p6)
            self.put_pixel(x+6, y, p7)
            self.put_pixel(x+7, y, p8)

            x += 8
            index += 1

    def step(self):
        """Renders one scanline."""
        self.window.pump_events()

        if not self.screen_on:
            return

        if self.background_display:
            self.read_palette()
            self.render_background_scanline(self.LY)

        if self.ly_rollover():
            self.show_viewport()
            self.window.update()
            self.calc_fps()
            self.window.clear(0x474741)

    @property
    def LCDCONT(self):
        return self._LCDCONT

    @LCDCONT.setter
    def LCDCONT(self, value):
        self._LCDCONT = value % 0xff
        log("LCDCONT display=%s background=%s" % ("on" if self.screen_on
            else "off", "on" if self.background_display else "off"))

    @property
    def screen_on(self):
        return (self._LCDCONT & (1<<7)) !=0

    @property
    def tile_table_address(self):
        """Returns current tile table address and whether it is signed."""
        if (self._LCDCONT & (1<<3)) == 0:
            return 0x9800, False
        else:
            return 0x9c00, True

    @property
    def tile_data_address(self):
        if (self._LCDCONT & (1<<4)) == 0:
            return 0x8800
        else:
            return 0x8000

    @property
    def background_display(self):
        return (self._LCDCONT & 1) == 1
