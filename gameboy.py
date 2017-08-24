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
import sys

# Maps opcode to
#   - (name, arguments ...)
#   - bytelength
#   - cycle duration
#   - affected flags (always in ZHNC order; 0 means reset after run)
opcodes = {
    0x00: ("NOP",           1,  4, None),
    0x01: ("LD BC",         3, 12, None),
    0x02: ("LD (BC), A",    1,  8, None),
    0x03: ("INC BC",        1,  8, None),
    0x04: ("INC B",         1,  4, ("Z", "0", "H")),
    0x05: ("DEC B",         1,  4, ("Z", "1", "H")),
    0x06: ("LD B",          2,  8, None),
    0x10: ("STOP 0",        2,  4, None),
    0x20: ("LD (BC), A",    1,  8, None),
    0x21: ("LD HL",         3, 12, None),
    0x31: ("LD SP",         3, 12, None),
    0x32: ("LD (HL-), A",   1,  8, None),
    0x76: ("HALT",          1,  4, None),
    0x9f: ("SBC A, A",      1,  4, ("Z", "1", "H", "C")),
    0xaf: ("XOR A",         1,  4, ("Z", "0", "0", "0")),
    0xcb: ("PREFIX CB",     1,  4, None),
    0xfb: ("EI",            1,  4, None),
    0xfe: ("CP",            2,  8, ("Z", "1", "H", "C")),
    0xff: ("RST 38H",       1, 16, None),
}

# Opcodes after the prefix opcode 0xCB has been encountered.
# Byte lengths here are WITHOUT the preceding prefix opcode 0xcb
extended_opcodes = {
    0x7c: ("BIT 7, H",      1, 8, ("Z", "0", "1")),
}

def load_binary(filename):
    with open(filename, "rb") as f:
        return array("B", f.read())

def disassemble(code):
    index = 0
    prefix = False

    while index < len(code):
        try:
            opcode = code[index]
            table = opcodes if not prefix else extended_opcodes
            name, bytelen, cycles, flags = table[opcode]
        except KeyError as e:
            raise KeyError("Unknown %sopcode 0x%0.2X" % ( "prefix-" if prefix else
                "", int(str(e))))

        if not prefix:
            sys.stdout.write("0x%0.4x:  " % index)
            raw = ""

        for byte in code[index:index+bytelen]:
            raw += "0x%0.2x " % byte

        arg = 0
        for offset in range(1, bytelen):
            arg |= code[index + offset] << 8*(offset-1)

        instruction = name
        if bytelen > 1:
            instruction += ", 0x%x" % arg

        if opcode != 0xcb:
            sys.stdout.write("%-20s " % raw)
            sys.stdout.write("%-18s" % instruction)

            if flags is not None:
                sys.stdout.write(" flags %s" % " ".join(flags))

            prefix = False
            sys.stdout.write("\n")
        else:
            prefix = True

        index += bytelen

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

    print("Boot ROM disassembly\n")
    disassemble(boot_rom)

if __name__ == "__main__":
    main()
