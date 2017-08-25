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
import random
import sys
from opcodes import opcodes, extended_opcodes, add_0xff00_opcodes

def load_binary(filename):
    """Reads a binary file image into an unsigned 8-bit array."""
    with open(filename, "rb") as f:
        return array("B", f.read())

def unsigned8_to_signed(value):
    if value > 127:
        return -(256 - value)
    else:
        return value

def format_hex(value):
    """Formats hex value suitable for disassembly."""
    sign = "" if value>=0 else "-"
    if abs(value) <= 0xff:
        return "%s$%0.2x" % (sign, abs(value))
    else:
        return "%s$%0.4x" % (sign, abs(value))

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
    def __init__(self, memory_controller):
        self.memory = memory_controller
        self.MHz = 4.194304

        # Registers
        self.A = 0
        self.B = 0
        self.C = 0
        self.D = 0
        self.E = 0
        self.F = 0 # flags register
        self.H = 0
        self.L = 0
        self.pc = 0
        self.sp = 0

    @property
    def zero_flagged(self):
        return (self.flags & 7) != 0

    @property
    def subtract_flagged(self):
        return (self.flags & 6) != 0

    @property
    def half_carry_flagged(self):
        return (self.flags & 5) != 0

    @property
    def carry_flagged(self):
        return (self.flags & 4) != 0

    def fetch(self):
        opcode = self.memory[self.pc]
        return opcode

    def decode(self, opcode):
        # Decode opcode
        name, bytelen, cycles, flags = opcodes[int(opcode)]

        # Decode arguments
        arg = None
        if bytelen > 1:
            arg = 0
            for offset in range(1, bytelen):
                arg |= self.memory[self.pc + offset] << 8*(offset-1)

            # TODO: Use disassembler to get a nicely formatted instruction
            if "d8" in name:
                name = name.replace("d8", format_hex(arg))
            elif "d16" in name:
                name = name.replace("d16", format_hex(arg))
            elif "a8" in name:
                if opcode in add_0xff00_opcodes:
                    name = name.replace("a8", "$ff00+$%0.2x" % arg)
                    arg += 0xff00
                else:
                    name = name.replace("a8", format_hex(arg))
            elif "a16" in name:
                name = name.replace("a16", "addr $%0.4x" % arg)
            elif "r8" in name:
                # 8-bit signed data, which are added to program counter
                value = unsigned8_to_signed(arg)
                abs_addr = address + bytelen + value
                if value < 0:
                    name = name.replace("r8", "PC-$%0.4x (@$%0.4x)" % (-value,
                        abs_addr))
                else:
                    name = name.replace("r8", "PC+$%0.4x (@$%0.4x)" % (value,
                        abs_addr))
            else:
                raise RuntimeError(
                    "Opcode 0x%0.2x %r has unspecified argument: %s" %
                        (opcode, name, format_hex(arg)))

        self.pc += bytelen
        return name, bytelen, cycles, flags, arg

    def step(self):
        address = self.pc
        opcode = self.fetch()
        name, bytelen, cycles, flags, arg = self.decode(opcode)

        if flags is None:
            flags = None

        print("$%0.4x:  0x%0.2x  %s flags: %s" % (address, opcode, name,
            flags))
        print("pc=$%0.4x sp=$%0.4x A=$%x B=$%x C=$%x D=$%x E=$%x F=$%x H=$%x L=$%x" %
                (self.pc, self.sp, self.A, self.B, self.C, self.D, self.E,
                    self.F, self.H, self.L))

        # TODO: Decode additional arguments, extended opcodes, etc., then
        # execute the instruction.

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

class MemoryController(object):
    def __init__(self, boot_rom, display, cartridge):
        self.ram = random_bytes(8000)
        self.display = display
        self.cartridge = cartridge
        self.boot_rom = boot_rom

        # On startup, copy code from boot rom into ordinary ram
        self.ram[:len(boot_rom)] = boot_rom
        self.booting = True

    def __getitem__(self, address):
        """Reads one memory byte."""
        assert(0 <= address <= 0xffff)

        if address < 0x8000:
            if self.booting:
                # TODO: I think the bank switching may come into play here.
                # Investigate.
                return self.ram[address]
            else:
                return self.cartridge.rom[address]
        elif address < 0xa000:
            return self.display.ram[address-0x8000]
        elif address < 0xc000:
            return self.ram[address-0xa000]

    def __setitem__(self, address, values):
        """Writes one or several bytes in memory."""
        assert(0 <= address <= 0xffff)
        assert(value <= 0xff)

        if address < 0x8000:
            if self.booting:
                if address < 256:
                    raise RuntimeError("Attempt to write into boot ROM")
            self.cartridge.rom[address] = values
        elif address < 0xa000:
            self.display.ram[address-0x8000] = values
        elif address < 0xc000:
            self.ram[address-0xa000] = values

    def get16(self, address):
        return self[address, 2]

    def set16(self, address, value):
        assert(value <= 0xffff)
        values = [(value & 0xff00) >> 16, value & 0xff]
        self[address] = values

class Gameboy(object):
    def __init__(self, cartridge, boot_rom):
        self.boot_rom = boot_rom
        self.cartridge = cartridge

        self.display = Display()
        self.memory = MemoryController(self.boot_rom, self.display,
                self.cartridge)
        self.cpu = CPU(self.memory)

    def __repr__(self):
        return "<Gameboy: %d bytes boot ROM>" % len(self.boot_rom)
