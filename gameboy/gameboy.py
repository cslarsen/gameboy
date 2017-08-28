from cpu import CPU
from display import Display
from memory import MemoryController

class Gameboy(object):
    def __init__(self, cartridge, boot_rom, no_display=False):
        self.boot_rom = boot_rom
        self.cartridge = cartridge

        self.display = Display(no_display=no_display)
        self.memory = MemoryController(self.boot_rom, self.display,
                self.cartridge)
        self.cpu = CPU(self.memory)
