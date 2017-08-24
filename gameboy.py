#! /usr/bin/env python
# -*- encoding: utf-8 -*-

"""
A Gameboy Emulator.

Implementation notes:

    * On power up, all RAM is set to random values. This is how a real Gameboy
    works, and I want to emulate that (e.g., custom made programs will have to
    clear out memory first. I'd like this emulator to behave like that.)
"""

__author__ = "Christian Stigen Larsen"
__copyright__ = "Copyright 2017 Christian Stigen Larsen"
__license__ = "The GNU GPL v3 or later"
__version__ = "0.1"

from array import array
import os
import random

# Maps opcode to
#   - name
#   - bytelength
#   - cycle duration
#   - affected flags
opcodes = {
    0x00: ("NOP", 1, 4, None),
    0x01: ("LD BC, d16", 3, 12, None),
    0x02: ("LD (BC), A", 1, 8, None),
    0x03: ("INC BC", 1, 8, None),
    0x04: ("INC B", 1, 4, ["Z", "0", "H"]),
    0x05: ("DEC B", 1, 4, ["Z", "1", "H"]),
    0x06: ("LD B, d8", 2, 8, None),
    #...
    0x31: ("LD SP, d16", 3, 12, None),
    0xaf: ("XOR A", 1, 4, ["Z", "0", "0", "0"]),
    0xfe: ("CP d8", 2, 8, ["Z", "1", "H", "C"]),
}

def load_binary(filename):
    with open(filename, "rb") as f:
        return array("B", f.read())

def disassemble(code):
    index = 0
    while index < len(code):
        current = code[index]
        opcode, bytelen, cycles, flags = opcodes[current]
        print("pos %d, raw 0x%x: %s" % (index, current, opcode))
        for index in range(index+1, index+bytelen):
            argument = code[index]
            print("pos %d, argument raw 0x%x" % (index, argument))
        index += 1

def random_bytes(length):
    """Returns random integers in the range 0-255."""
    r = array("B")
    for i in range(length):
        r.append(random.randint(0x00, 0xff))
    return r

class CPU(object):
    """
    An 8-bit Sharp LR35902 CPU running at 4.19 MHz.

    This CPU is very similar to the Intel 8080 and the Zilog Z80.
    """
    def __init__(self):
        self.MHz = 4.194304

class Display(object):
    def __init__(self):
        self.ram = random_bytes(8000)
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
        self.rom = array("B", [0]*32000) if rom is None else rom
        assert(len(self.rom) >= 32000)

class Gameboy(object):
    def __init__(self, cartridge, boot_rom):
        self.bootstrap_rom = boot_rom
        self.cartridge = cartridge
        self.cpu = CPU()
        self.display = Display()
        self.ram = random_bytes(8000)

    def __repr__(self):
        return "<Gameboy: %d bytes boot ROM>" % len(self.bootstrap_rom)

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
    boot_file = os.path.join(os.path.dirname(__file__), "roms", "boot")
    boot_rom = load_binary(boot_file)

    gameboy = Gameboy(Cartridge(), boot_rom)
    print(gameboy)

    print("Boot ROM disassembly:")
    disassemble(boot_rom)

if __name__ == "__main__":
    main()
