from cpu import CPU
from display import Display
from memory import MemoryController

class Gameboy(object):
    def __init__(self, cartridge, boot_rom):
        self.boot_rom = boot_rom
        self.cartridge = cartridge

        self.display = Display()
        self.memory = MemoryController(self.boot_rom, self.display,
                self.cartridge)
        self.cpu = CPU(self.memory)
