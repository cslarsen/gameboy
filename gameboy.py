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
#
# The mnemonics follow http://pastraiser.com/cpu/gameboy/gameboy_opcodes.html
#
# NOTE: Instruction 0xe2 is said to take two bytes (one 8-bit argument), but
# from elsewhere it seems like it only takes one. For example, see
# https://stackoverflow.com/a/41422692/21028
#
opcodes = {
    0x00: ("NOP",               1,  4, None),
    0x01: ("LD BC, d16",        3, 12, None),
    0x02: ("LD (BC), A",        1,  8, None),
    0x03: ("INC BC",            1,  8, None),
    0x04: ("INC B",             1,  4, ("Z", "0", "H")),
    0x05: ("DEC B",             1,  4, ("Z", "1", "H")),
    0x06: ("LD B",              2,  8, None),
    0x0c: ("INC C",             1,  4, ("Z", "0", "H")),
    0x0e: ("LD C, d8",          2,  8, None),
    0x10: ("STOP",              2,  4, None),
    0x20: ("LD (BC), A",        1,  8, None),
    0x21: ("LD HL, d16",        3, 12, None),
    0x31: ("LD SP, d16",        3, 12, None),
    0x32: ("LD (HL-), A",       1,  8, None),
    0x3e: ("LD A, d8",          2,  8, None),
    0x76: ("HALT",              1,  4, None),
    0x77: ("LD (HL), A",        1,  8, None),
    0x9f: ("SBC A, A",          1,  4, ("Z", "1", "H", "C")),
    0xaf: ("XOR A",             1,  4, ("Z", "0", "0", "0")),
    0xcb: ("PREFIX CB",         1,  4, None),
    0xe0: ("LDH (a8), A",       2, 12, None), # NOTE: Others say LD, not LDH
    0xe2: ("LD ($ff00+C), A",   1,  8, None), # NOTE: Above link says 2 bytes!
    0xfb: ("EI",                1,  4, None), # TODO: JR NZ, ??
    0xfe: ("CP d8",             2,  8, ("Z", "1", "H", "C")),
    0xff: ("RST 38H",           1, 16, None),
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
            raise KeyError("Unknown %sopcode $%0.2x" % ( "prefix-" if prefix else
                "", int(str(e))))

        if not prefix:
            sys.stdout.write("$%0.4x:  " % index)
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
                name = name.replace("d8", "$%0.2x" % value)
            elif "d16" in name:
                # immediate data
                value = arg
                name = name.replace("d16", "$%0.2x" % value)
            elif "a8" in name:
                # 8-bit unsigned data, which are added to 0xFF00 in certain
                # instructions (replacement for missing IN and OUT
                # instructions)
                # TODO: Add to 0xff00 where applicable
                value = arg
                if opcode == 0xe0:
                    value += 0xff00
                    name = name.replace("a8", "$ff00+$%0.2x" % arg)
                else:
                    name = name.replace("a8", "$%0.2x" % arg)
            elif "a16" in name:
                # 16-bit address
                value = arg
                name = name.replace("a16", "addr $%x" % value)
            elif "r8" in name:
                # 8-bit signed data, which are added to program counter
                # TODO: Implement signedness
                value = 0x7f - arg # TODO: Correct?
                name = name.replace("r8", "pc + %s$%x" % ("-" if value<0 else
                    "+"))
            else:
                raise RuntimeError(
                    "Opcode 0x%0.4x %r has unspecified argument: %s" %
                        (opcode, name, arg))

        if opcode != 0xcb:
            sys.stdout.write("%-20s " % raw)
            instruction = name + instruction
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
