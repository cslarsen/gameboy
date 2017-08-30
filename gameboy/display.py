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
        self.zoom = zoom
        self.width = 256
        self.height = 256

        sdl2.ext.init()

        self.window = sdl2.ext.Window(title=title, size=(self.width*self.zoom,
            self.height*self.zoom))

        # Use SDL2 hardware acceleration
        self.renderer = sdl2.ext.Renderer(self.window,
                flags = sdl2.SDL_RENDERER_ACCELERATED
                      | sdl2.SDL_RENDERER_PRESENTVSYNC)

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

        self.measured_fps = []
        self.start = time.clock()

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
        #assert(color < 4)
        self.window.put(x, y, self.palette_to_rgb(color))

    def inc_ly(self):
        self.LY = (self.LY + 1) % 0x100

    def show_viewport(self):
        """Marks viewable area"""
        self.window.box(self.SCX, self.SCY, self.width, self.height)

    def calc_fps(self):
        now = time.clock()
        elapsed = now - self.start
        if elapsed < 1:
            return

        self.start = now
        self.measured_fps.append(1.0/elapsed)
        counts = 3

        if len(self.measured_fps) > counts:
            self.measured_fps = self.measured_fps[-counts:]
            avg_fps = sum(self.measured_fps) / float(len(self.measured_fps))
            avg_spf = 1.0/avg_fps
            log("avg %.2f fps (%.2fs per frame)\r" % (avg_fps, avg_spf),
                    nl=False)

    def step(self):
        self.window.pump_events()

        if self.screen_on:
            self.read_palette()
            if self.background_display:
                self.render_background()

        if self.LY == 144:
            self.show_viewport()
            self.window.update()
            self.calc_fps()
            self.window.clear(0)
        self.inc_ly()

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
        table = self.tile_table_address

        # Tile bitmap data
        data = self.tile_data_address
        signed = table == 0x9c00

        xpos, ypos = 0, 0
        for tile_index in range(32*32):
            if ypos == self.LY: # poor man's scanline drawing (fix later)
                tile_number = self.ram[table + tile_index - self.ram.offset]
                if signed:
                    tile_number = u8_to_signed(tile_number)

                # Get the tile bitmap; 8x8 pixels stored as 2-bit colors
                # meaning 16 bytes of memory
                bitmap = []
                line = []

                n = 0
                while n < 16:
                    b1 = self.ram[data + tile_number*16 + n - self.ram.offset]
                    b2 = self.ram[data + tile_number*16 + n + 1 - self.ram.offset]
                    n += 2

                    p1 = ((b1 & 0b00000001) >> 0) | ((b2 & 0b00000001) << 1)
                    p2 = ((b1 & 0b00000010) >> 1) | ((b2 & 0b00000010) >> 0)
                    p3 = ((b1 & 0b00000100) >> 2) | ((b2 & 0b00000100) >> 1)
                    p4 = ((b1 & 0b00001000) >> 3) | ((b2 & 0b00001000) >> 2)
                    p5 = ((b1 & 0b00010000) >> 4) | ((b2 & 0b00010000) >> 3)
                    p6 = ((b1 & 0b00100000) >> 5) | ((b2 & 0b00100000) >> 4)
                    p7 = ((b1 & 0b01000000) >> 6) | ((b2 & 0b01000000) >> 5)
                    p8 = ((b1 & 0b10000000) >> 7) | ((b2 & 0b10000000) >> 6)

                    bitmap.append([p8, p7, p6, p5, p4, p3, p2, p1])

                bitmap[0][0] = 999
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
                if ypos == 256:
                    break

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
        if (self._LCDCONT & (1<<3)) == 0:
            return 0x9800
        else:
            return 0x9c00

    @property
    def tile_data_address(self):
        if (self._LCDCONT & (1<<4)) == 0:
            return 0x8800
        else:
            return 0x8000

    @property
    def background_display(self):
        return (self._LCDCONT & 1) == 1
