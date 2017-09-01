"""
Implementation of the GameBoy CPU.

We will start the program counter at address zero, unlike 0x0100, since we have
a 256-byte boot ROM. After booting, it will continue executing from 0x0100.

TODO: Implement bytes and registers as rollover unsigned ints.
"""

import sys
import time

from util import (
    format_bin,
    format_hex,
    log,
    u16_to_u8,
    u8_to_signed,
    u8_to_u16,
)

from opcodes import (
    add_0xff00_opcodes,
    extended_opcodes,
    opcodes,
    TYPE_R8,
)

class CPU(object):
    """
    An 8-bit Sharp LR35902 CPU running at 4.19 MHz.

    This CPU is very similar to the Intel 8080 and the Zilog Z80.
    """
    def __init__(self, memory_controller):
        self.memory = memory_controller
        self.MHz = 4.194304

        # 8-bit registers
        self.A = 0
        self.B = 0
        self.C = 0
        self.D = 0
        self.E = 0
        self.F = 0 # flags register
        self.H = 0
        self.L = 0

        # 16-bit registers
        self.PC = 0
        self.SP = 0

        # Amount of cycles spent
        self.cycles = 0
        self.total_cycles = 0
        self.start = time.clock()

    def fetch(self):
        opcode = self.memory[self.PC]
        return opcode

    def decode(self, opcode):
        # Decode opcode
        name, bytelen, type, cycles, flags = opcodes[opcode]
        raw = [opcode]

        if opcode == 0xcb:
            # Prefix: Fetch extended opcode
            self.PC += bytelen
            opcode = self.fetch()
            raw.append(opcode)

            name, bytelen, type, xcycles, flags = extended_opcodes[opcode]
            cycles += xcycles

        # Decode arguments
        arg = None
        if bytelen > 1:
            arg = 0
            for offset in range(1, bytelen):
                byte = self.memory[self.PC + offset]
                raw.append(byte)
                arg |= byte << 8*(offset-1)

            if type == TYPE_R8:
                arg = u8_to_signed(arg)

            if opcode in add_0xff00_opcodes:
                arg += 0xff00

        # TODO: Handle extended opcodes

        self.PC += bytelen
        return name, opcode, bytelen, cycles, flags, arg, raw

    def run(self):
        while True:
            self.step()

    def step(self):
        address = self.PC
        opcode = self.fetch()
        name, opcode, length, cycles, flags, arg, raw = self.decode(opcode)

        self.execute(opcode, length, cycles, flags, raw, arg)

        # Let the display do its thing, timed *very* roughly
        ratio = int((self.MHz*1e6 / self.memory.display.fps) /
                self.memory.display.scanlines)

        if self.cycles >= ratio:
            self.cycles %= ratio
            self.memory.display.step()

    @property
    def emulated_MHz(self):
        """Attempts to measure emulated clockspeed."""
        elapsed = (time.clock() - self.start)
        if elapsed == 0:
            return 0
        cps = self.total_cycles / elapsed
        return cps / 1000000.0

    def print_registers(self):
        print("pc=$%0.4x sp=$%0.4x a=$%0.2x b=$%0.2x c=$%0.2x d=$%0.2x e=$%0.2x f=$%0.1x h=$%0.2x l=$%0.2x" %
                (self.PC, self.SP, self.A, self.B, self.C, self.D, self.E,
                    self.F, self.H, self.L))

        flags = "%s%s%s%s" % ("Z" if self.Z_flag else "-",
                "N" if self.N_flag else "-",
                "H" if self.H_flag else "-",
                "C" if self.C_flag else "-")
        print("flags=%s cycles=%d ~%.1f MHz" % (flags, self.total_cycles,
            self.emulated_MHz))

    @property
    def HL(self):
        return u8_to_u16(self.H, self.L)

    @HL.setter
    def HL(self, value):
        self.H, self.L = u16_to_u8(value)

    @property
    def DE(self):
        return u8_to_u16(self.D, self.E)

    @DE.setter
    def DE(self, value):
        self.D, self.E = u16_to_u8(value)

    @property
    def BC(self):
        return u8_to_u16(self.B, self.C)

    @BC.setter
    def BC(self, value):
        self.B, self.C = u16_to_u8(value)

    @property
    def Z_flag(self):
        """The zero flag."""
        return (self.F & 0b10000000) >> 7

    @Z_flag.setter
    def Z_flag(self, value):
        if value:
            self.F |= 1<<7
        else:
            self.F &= ~(1<<7)

    @property
    def N_flag(self):
        """The subtract flag."""
        return (self.F & 0b01000000) >> 6

    @N_flag.setter
    def N_flag(self, value):
        if value:
            self.F |= 1<<6
        else:
            self.F &= ~(1<<6)

    @property
    def H_flag(self):
        """The half carry flag"""
        return (self.F & 0b00100000) >> 5

    @H_flag.setter
    def H_flag(self, value):
        if value:
            self.F |= 1<<5
        else:
            self.F &= ~(1<<5)

    @property
    def C_flag(self):
        """The carry flag"""
        return (self.F & 0b00010000) >> 4

    @C_flag.setter
    def C_flag(self, value):
        if value:
            self.F |= 1<<4
        else:
            self.F &= ~(1<<4)

    def execute(self, opcode, length, cycles, flags, raw, arg=None):
        # TODO: By changing the opcodes struct, we can do this programmatically
        # and much more elegantly
        if length == 1:
            assert(arg is None)
        else:
            assert(arg is not None)

        zero = None
        carry = None
        half_carry = None
        subtract = None

        def error_message(prefix):
            message = "%s instruction %s" % (
                    prefix,
                    " ".join(map(lambda x: "0x%0.2x" % x, raw)))
            if arg is not None:
                message += " with argument %s" % format_hex(arg)
            return message

        def unknown_opcode():
            return RuntimeError("$%0.4x: %s\n" % (self.PC,
                error_message("Unknown")))

        def not_implemented():
            return NotImplementedError(error_message("Not implemented"))

        # Order dependency: Check for prefix first
        if raw[0] == 0xcb: # PREFIX CB
            if opcode == 0x11: # RL C
                carry = (self.C & (1<<7)) >> 7
                self.C = (self.C << 1) & 0xff
                self.C |= self.C_flag
                zero = (self.C == 0)
            elif opcode == 0x7c: # BIT 7, H
                zero = not (self.H & (1<<7))
            else:
                raise unknown_opcode()
        else:
            # TODO: See the official Nintendo manual. Instructions can be
            # grouped much better. For example, all load instructions start
            # with bits 01, then the next three bits is destination register
            # (e.g. A=0b111) then the source register is the three last bits,
            # from a table. Makes dispatching much faster as well.
            if opcode == 0x00: # NOP
                pass

            elif opcode == 0xaf: # XOR A
                self.A = 0
                zero = True

            elif opcode == 0x3e: # LD A, d8
                self.A = arg

            elif opcode == 0x21: # LD HL, d16
                self.HL = arg

            elif opcode == 0x31: # LD SP, d16
                self.SP = arg

            elif opcode == 0x32: # LD (HL-), A
                self.memory[self.HL] = self.A
                self.HL = (self.HL - 1) % 0xffff

            elif opcode == 0x77: # LD (HL), A
                self.memory[self.HL] = self.A

            elif opcode == 0x78: # LD A, B
                self.A = self.B

            elif opcode == 0x7b: # LD A, E
                self.A = self.E

            elif opcode == 0x7c: # LD A, H
                self.A = self.H

            elif opcode == 0x7d: # LD A, L
                self.A = self.L

            elif opcode == 0xe2: # LD ($ff00+C), A
                self.memory[(0xff00 + self.C) % 0xffff] = self.A

            elif opcode == 0xe0: # LDH ($ff00+a8), A
                self.memory[arg] = self.A

            elif opcode == 0x01: # LD BC, d16
                self.BC = arg

            elif opcode == 0x02: # LD (BC), A
                self.memory[self.BC] = self.A

            elif opcode == 0x04: # INC B
                self.B = (self.B + 1) % 0xff
                zero = (self.B == 0)
                # TODO: Set half carry

            elif opcode == 0x05: # DEC B
                self.B = (self.B - 1) % 0xff
                zero = (self.B == 0)
                # TODO: Implement half-carry flag

            elif opcode == 0x06: # LD B, d8
                self.B = arg

            elif opcode == 0x08: # LD (a16), SP
                self.memory.set16(arg, self.SP)

            elif opcode == 0x0b: # DEC BC
                self.BC = (self.BC - 1) % 0xffff

            elif opcode == 0x0c: # INC C
                self.C = (self.C + 1) % 0xff
                zero = (self.C == 0)
                # TODO: Set half carry

            elif opcode == 0x0d: # DEC C
                self.C = (self.C - 1) % 0xff
                zero = (self.C == 0)
                # TODO: set half_carry flag

            elif opcode == 0x0e: # LD C, d8
                self.C = arg

            elif opcode == 0x10: # STOP
                raise not_implemented()

            elif opcode == 0x11: # LD DE, d16
                self.DE = arg

            elif opcode == 0x13: # INC DE
                self.DE = (self.DE + 1) % 0xffff

            elif opcode == 0x15: # DEC D
                self.D = (self.D - 1) % 0xff
                zero = (self.D == 0)
                # TODO: set half_carry flag

            elif opcode == 0x16: # LD D, d8
                self.D = arg

            elif opcode == 0x17: # RLA
                carry = (self.A & (1<<7)) >> 7
                self.A = (self.A << 1) & 0xff
                self.A |= self.C_flag
                zero = (self.A == 0)

            elif opcode == 0x1a: # LD A, (DE)
                self.A = self.memory[self.DE]

            elif opcode == 0x1d: # DEC E
                self.E = (self.E - 1) % 0xff
                zero = (self.E == 0)
                # TODO: set half_carry flag

            elif opcode == 0x1e: # LD E, d8
                self.E = arg

            elif opcode == 0x22: # LD (HL+), A
                self.memory[self.HL] = self.A
                self.HL = (self.HL + 1) % 0xffff

            elif opcode == 0x23: # INC HL
                self.HL = (self.HL + 1) % 0xffff

            elif opcode == 0x24: # INC H
                self.H = (self.H + 1) % 0xff
                zero = (self.H == 0)
                # TODO: Set half carry

            elif opcode == 0x18: # JR r8
                self.PC = (self.PC + arg) % 0xffff

            elif opcode == 0x28: # JR Z, r8
                if self.Z_flag:
                    cycles = cycles[0]
                    self.PC = (self.PC + arg) % 0xffff
                else:
                    cycles = cycles[1]

            elif opcode == 0x20: # JR NZ, r8
                if self.Z_flag:
                    cycles = cycles[1]
                else:
                    cycles = cycles[0]
                    self.PC = (self.PC + arg) % 0xffff

            elif opcode == 0x2e: # LD L, d8
                self.L = arg

            elif opcode == 0x33: # INC SP
                self.SP = (self.SP + 1) % 0xffff
                zero = (self.SP == 0)
                # TODO: Set half_carry flag

            elif opcode == 0x3c: # INC A
                self.A = (self.A + 1) % 0xff
                zero = (self.A == 0)
                # TODO: set half carry

            elif opcode == 0x3d: # DEC A
                self.A = (self.A - 1) % 0xff
                zero = (self.A == 0)
                # TODO: set half_carry flag

            elif opcode == 0x42: # LD B, D
                self.B = self.D

            elif opcode == 0x4f: # LD C, A
                self.C = self.A

            elif opcode == 0x57: # LD D, A
                self.D = self.A

            elif opcode == 0x63: # LD H, E
                self.H = self.E

            elif opcode == 0x66: # LD H, (HL)
                self.H = self.memory[self.HL]

            elif opcode == 0x67: # LD H, A
                self.H = self.A

            elif opcode == 0x6e: # LD L, (HL)
                self.L = self.memory[self.HL]

            elif opcode == 0x73: # LD (HL), E
                self.memory[self.HL] = self.E

            elif opcode == 0x76: # HALT
                raise not_implemented()

            elif opcode == 0xc1: # POP BC
                self.SP = (self.SP + 0x10) % 0xffff
                self.BC = self.memory.get16(self.SP)

            elif opcode == 0xc5: # PUSH BC
                self.memory.set16(self.SP, self.BC)
                self.SP = (self.SP - 0x10) % 0xffff

            elif opcode == 0xc9: # RET
                self.SP = (self.SP + 0x10) % 0xffff
                self.PC = self.memory.get16(self.SP)

            elif opcode == 0xcc: # CALL Z, a16
                if self.Z_flag:
                    self.memory.set16(self.SP, self.PC)
                    self.SP = (self.SP - 0x10) % 0xffff
                    self.PC = arg
                    cycles = cycles[0]
                else:
                    cycles = cycles[1]

            elif opcode == 0xcd: # CALL a16
                self.memory.set16(self.SP, self.PC)
                self.SP = (self.SP - 0x10) % 0xffff
                self.PC = arg

            elif opcode == 0xce: # ADD A, d8
                raise not_implemented()

            elif opcode == 0xd9: # RETI
                raise not_implemented()

            elif opcode == 0xea: # LD (a16), A
                self.memory[arg] = self.A

            elif opcode == 0xf0: # LDH A, (a8)
                self.A = self.memory[arg]

            elif opcode == 0xf3: # DI
                raise not_implemented()

            elif opcode == 0xf7: # RST 30H
                self.memory.set16(self.SP, self.PC)
                self.SP = (self.SP - 0x10) % 0xffff
                self.PC = self.memory[0x0030]

            elif opcode == 0xf9: # LD SP, HL
                self.SP = self.HL

            elif opcode == 0xfa: # LD A, (a16)
                self.A = self.memory[arg]

            elif opcode == 0xfb: # EI
                raise not_implemented()

            elif opcode == 0xfe: # CP d8
                result = (self.A - arg) % 0xff
                zero = (result == 0)
                carry = (self.A < arg)
                # TODO: set half_carry

            elif opcode == 0xff: # RST 38H
                self.memory.set16(self.SP, self.PC)
                self.SP = (self.SP - 0x10) % 0xffff
                self.PC = self.memory[0x0038]

            elif opcode == 0x90: # SUB B
                self.A = (self.A - self.B) % 0xff
                zero = (self.A == 0)
                # TODO: set half carry and carry flags

            elif opcode == 0xbe: # CP (HL)
                result = (self.A - self.memory[self.HL]) % 0xff
                zero = (result == 0)
                carry = (self.A < arg)
                # TODO: set half_carry

            elif opcode == 0x86: # ADD A, (HL)
                self.A = (self.A + self.memory[self.HL]) % 0xff
                zero = (self.A == 0)
                # TODO: Set other flags

            else:
                raise unknown_opcode()

        # Update flags after executing the instruction
        if flags is not None:
            for shift, flag in zip((7, 6, 5, 4), flags):
                if flag == "0":
                    self.F &= ~(1 << shift)
                elif flag == "1":
                    self.F |= 1<<shift
                elif flag == "Z" and zero is not None:
                    self.Z_flag = zero
                elif flag == "H" and half_carry is not None:
                    self.H_flag = half_carry
                elif flag == "N" and subtract is not None:
                    self.N_flag = subtract
                elif flag == "C" and carry is not None:
                    self.C_flag = carry

        self.cycles += cycles
        self.total_cycles += cycles
