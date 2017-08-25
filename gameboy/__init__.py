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

def disassemble(code, start_address=0x0000):
    """Disassembles binary code."""
    index = 0

    # Whether the previous instruciton was the 0xcb prefix opcode
    prefix = False

    while index < len(code):
        try:
            address = start_address + index
            opcode = code[index]
            table = opcodes if not prefix else extended_opcodes
            name, bytelen, cycles, flags = table[opcode]
        except KeyError as e:
            raise KeyError("Unknown %sopcode 0x%0.2x" % (
                "prefixed " if prefix else "", int(str(e))))

        if not prefix:
            sys.stdout.write("$%0.4x:  " % address)
            raw = ""

        for byte in code[index:index+bytelen]:
            raw += "0x%0.2x " % byte

        arg = 0
        for offset in range(1, bytelen):
            arg |= code[index + offset] << 8*(offset-1)

        instruction = ""
        if bytelen > 1:
            if "d8" in name:
                # immediate data
                value = arg
                name = name.replace("d8", format_hex(value))
            elif "d16" in name:
                # immediate data
                value = arg
                name = name.replace("d16", format_hex(value))
            elif "a8" in name:
                # 8-bit unsigned data, which are added to 0xFF00 in certain
                # instructions (replacement for missing IN and OUT
                # instructions)
                # TODO: Add to 0xff00 where applicable
                value = arg
                if opcode in add_0xff00_opcodes:
                    value += 0xff00
                    name = name.replace("a8", "$ff00+$%0.2x" % arg)
                else:
                    name = name.replace("a8", format_hex(arg))
            elif "a16" in name:
                # 16-bit address
                value = arg
                name = name.replace("a16", "addr $%0.4x" % value)
            elif "r8" in name:
                # 8-bit signed data, which are added to program counter
                value = unsigned8_to_signed(arg)

                # calculate absolute address: PC (program counter) + value,
                # where the PC is now at the next instruction
                abs_addr = address + bytelen + value

                # NOTE: For opcode 0x20, a disassembly says: "if $19 + bytes
                # from $0134-$014D  don't add to $00" Seems I get somewhat
                # different result from another disassembler for that
                # particular code (boot code, position $00fa), other says jump
                # to @$00fe instead of @$00fa). Actually, that listing's
                # instruction is supposed to lock up, and from my disassembly
                # it actually seems like the instruction jumps to itself
                # forever. So this one may actually be the correct one.

                if value < 0:
                    name = name.replace("r8", "PC-$%0.4x (@$%0.4x)" % (-value,
                        abs_addr))
                else:
                    name = name.replace("r8", "PC+$%0.4x (@$%0.4x)" %
                            (value, abs_addr))
            else:
                raise RuntimeError(
                    "Opcode 0x%0.2x %r has unspecified argument: %s" %
                        (opcode, name, format_hex(arg)))

        if opcode != 0xcb:
            sys.stdout.write("%-20s " % raw)
            instruction = name + instruction
            sys.stdout.write("%-24s" % instruction)

            if flags is not None:
                for flag in flags:
                    assert(flag in ("Z", "N", "H", "C", "0", "1"))
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
    def __init__(self, memory):
        self.MHz = 4.194304
        self._flags = 0
        self.stack_pointer = 0
        self.program_counter = 0
        self.register_A = 0
        self.register_B = 0
        self.register_C = 0
        self.register_D = 0
        self.register_E = 0
        self.register_H = 0
        self.register_L = 0
        self.memory = memory

    @property
    def flags(self):
        return self._flags

    @flags.setter
    def flags(self, value):
        assert(0 <= value <= 7)
        self._flags = value

    @property
    def zero_flagged(self):
        return (self._flags & 7) != 0

    @property
    def subtract_flagged(self):
        return (self._flags & 6) != 0

    @property
    def half_carry_flagged(self):
        return (self._flags & 5) != 0

    @property
    def carry_flagged(self):
        return (self._flags & 4) != 0

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
    def __init__(self, display, cartridge):
        self.ram = random_bytes(8000)
        self.display = display
        self.cartridge = cartridge

    def __getitem__(self, address, length=1):
        """Reads memory bytes."""
        assert(0 <= address <= 0xffff)

        if address < 0x8000:
            return self.cartridge.rom[address:address+length]
        elif address < 0xa000:
            return self.display.ram[address-0x8000:address-0x8000+length]
        elif address < 0xc000:
            return self.ram[address-0xa000:address-0xa000+length]

    def __setitem__(self, address, *values):
        """Writes one or several bytes in memory."""
        assert(0 <= address <= 0xffff)
        length = len(values)

        for value in values:
            assert(value <= 0xff)

        if address < 0x8000:
            self.cartridge.rom[address:address+length] = values
        elif address < 0xa000:
            self.display.ram[address-0x8000:address-0x8000+length] = values
        elif address < 0xc000:
            self.ram[address-0xa000:address-0xa000+length] = values

    def get16(self, address):
        return self[address, 2]

    def set16(self, address, value):
        assert(value <= 0xffff)
        values = [(value & 0xff00) >> 16, value & 0xff]
        self[address] = values

class Gameboy(object):
    def __init__(self, cartridge, boot_rom):
        self.bootstrap_rom = boot_rom
        self.cartridge = cartridge

        self.display = Display()
        self.memory = MemoryController(self.display, self.cartridge)
        self.cpu = CPU(self.memory)

    def __repr__(self):
        return "<Gameboy: %d bytes boot ROM>" % len(self.bootstrap_rom)
