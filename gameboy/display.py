from util import make_randomized_array

class Display(object):
    def __init__(self):
        self.ram = make_randomized_array(8000)
        self.vblank_duration = 1.1
        self.fps = 59.7

    @property
    def width(self):
        return 160

    @property
    def height(self):
        return 144
