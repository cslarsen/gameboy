#! /usr/bin/env python
# -*- encoding: utf-8 -*-

from array import array


class CPU(object):
    """An 8-bit Sharp LR35902 CPU running at 4.19 MHz."""
    def __init__(self):
        self.MHz = 4.194304

class Display(object):
    def __init__(self):
        self.ram = array("b", [0]*8000)
        self.vblank_duration = 1.1
        self.fps = 59.7

    @property
    def width(self):
        return 160

    @property
    def height(self):
        return 144

class Cartridge(object):
    def __init__(self, rom=None):
        self.rom = array("b", [0]*32000) if rom is None else rom
        assert(len(self.rom) >= 32000)

class Gameboy(object):
    def __init__(self, cartridge):
        self.bootstrap_rom = array("b", [0]*256)
        self.cartridge = cartridge
        self.cpu = CPU()
        self.display = Display()
        self.ram = array("b", [0]*8000)

    def peek(self, address, length=1):
        """Reads a byte in memory."""
        assert(0 <= address <= 0xffff)

        if address < 0x8000:
            return self.program_rom[address:address+length]
        elif address < 0xa000:
            return self.display.ram[address-0x8000:address-0x8000+length]
        elif address < 0xc000:
            return self.ram[address-0xa000:address-0xa000+length]

    def poke(self, address, *values):
        """Writes one or several bytes in memory."""
        assert(0 <= address <= 0xffff)

        if address < 0x8000:
            self.program_rom[address:address+length] = values
        elif address < 0xa000:
            self.display.ram[address-0x8000:address-0x8000+length] = values
        elif address < 0xc000:
            self.ram[address-0xa000:address-0xa000+length] = values

def main():
    gameboy = Gameboy(Cartridge())

if __name__ == "__main__":
    main()
