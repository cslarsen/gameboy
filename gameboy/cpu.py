"""
Implementation of the GameBoy CPU.

We will start the program counter at address zero, unlike 0x0100, since we have
a 256-byte boot ROM. After booting, it will continue executing from 0x0100.

TODO: Implement bytes and registers as rollover unsigned ints.
"""

import time

from util import (
    check_boot,
    format_hex,
    get16be,
    log,
    make_array,
    set16be,
    u16_to_u8,
    u8_to_signed,
    u8_to_u16,
)

from errors import (
    EmulatorError,
    InvalidOpcodeError,
    OpcodeError,
)

from opcodes import (
    add_0xff00_opcodes,
    extended_opcodes,
    opcodes,
    TYPE_R8,
)

from instructions import (
    inc16,
    swap8,
)

class Register8(object):
    def __init__(self, index):
        self.index = index

    def __get__(self, obj, objtype):
        return obj.registers[self.index]

    def __set__(self, obj, value):
        obj.registers[self.index] = value % 0x100

class Register16(object):
    def __init__(self, index):
        self.index = index

    def __get__(self, obj, objtype):
        return get16be(obj.registers, self.index)

    def __set__(self, obj, value):
        set16be(obj.registers, self.index, value)

class CPU(object):
    """
    An 8-bit Sharp LR35902 CPU running at 4.19 MHz.

    This CPU is very similar to the Intel 8080 and the Zilog Z80.
    """
    A = Register8(4)
    F = Register8(5)
    B = Register8(6)
    C = Register8(7)
    D = Register8(8)
    E = Register8(9)
    H = Register8(10)
    L = Register8(11)

    PC = Register16(0)
    SP = Register16(2)
    AF = Register16(4)
    BC = Register16(6)
    DE = Register16(8)
    HL = Register16(10)

    def __init__(self, memory_controller):
        self.memory = memory_controller
        self.MHz = 4.194304

        # 8-bit registers, implemented in an array, because it makes sense.
        # Layout:
        #   PC
        #   SP
        #   AF
        #   BC
        #   DE
        #   HL
        self.registers = make_array([0]*12)

        # Interrupts Maske Enable flag
        # TODO: Implement all flags and the rest of the interrupt system
        self.IME = False

        # Amount of cycles spent
        self.cycles = 0
        self.total_cycles = 0
        self.start = time.clock()

        self.screen_cycles = int((self.MHz*1e6 / self.memory.display.fps) /
                self.memory.display.scanlines)

    def push(self, nn):
        self.memory.set16(self.SP, nn)
        self.SP -= 2

    def pop(self):
        self.SP += 2
        return self.memory.get16(self.SP)

    def call(self, nn):
        self.push(self.PC)
        self.PC = nn

    def ret(self):
        self.PC = self.pop()

    def jmp(self, nn):
        self.PC = nn

    def rst(self, nn):
        self.call(self.memory.get16(nn))

    def fetch(self):
        opcode = self.memory[self.PC]
        return opcode

    def decode(self, opcode):
        # Decode opcode
        try:
            name, bytelen, type, cycles, flags = opcodes[opcode]
        except KeyError:
            raise OpcodeError("Unknown opcode 0x%0.2x at $%0.4x" % (opcode,
                self.PC))

        raw = [opcode]

        if opcode == 0xcb:
            # Prefix: Fetch extended opcode
            self.PC += bytelen
            opcode = self.fetch()
            raw.append(opcode)

            name, bytelen, type, xcycles, flags = extended_opcodes[opcode]
            cycles += xcycles
        elif opcode == 0x10:
            # Prefix: Stop opcode
            self.PC += bytelen
            opcode = self.fetch()
            raw.append(opcode)

            # It is stored in the default table as just 0x10, so just get it
            # from there. I prefer decoding it like "0x10 0x00 STOP" instead of
            # two instructions STOP/NOP.
            name, bytelen, type, xcycles, flags = opcodes[0x10]
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
        start = self.PC
        boot_rom = self.memory.boot_rom_active

        try:
            opcode = self.fetch()
            name, opcode, length, cycles, flags, arg, raw = self.decode(opcode)
            self.execute(opcode, length, cycles, flags, raw, arg)

            # Let the display do its thing, timed *very* roughly
            if self.cycles >= self.screen_cycles:
                self.cycles %= self.screen_cycles
                self.memory.display.step()

            if boot_rom and not self.memory.boot_rom_active:
                if not check_boot(self):
                    raise EmulatorError("Boot state not OK")
        except Exception:
            log("** Exception at $%0.4x" % start)
            raise

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
    def Z_flag(self):
        """The zero flag."""
        return (self.F & 0b10000000) >> 7

    @Z_flag.setter
    def Z_flag(self, value):
        if value:
            self.F |= 1<<7
        else:
            self.F &= 0b01111111

    @property
    def N_flag(self):
        """The subtract flag."""
        return (self.F & 0b01000000) >> 6

    @N_flag.setter
    def N_flag(self, value):
        if value:
            self.F |= 1<<6
        else:
            self.F &= 0b10111111

    @property
    def H_flag(self):
        """The half carry flag"""
        return (self.F & 0b00100000) >> 5

    @H_flag.setter
    def H_flag(self, value):
        if value:
            self.F |= 1<<5
        else:
            self.F &= 0b11011111

    @property
    def C_flag(self):
        """The carry flag"""
        return (self.F & 0b00010000) >> 4

    @C_flag.setter
    def C_flag(self, value):
        if value:
            self.F |= 1<<4
        else:
            self.F &= 0b11101111

    def error_message(self, prefix, raw=None, arg=None):
        if raw is None:
            raw = []
        message = "%s instruction %s" % (prefix, " ".join(map(lambda x:
            "0x%0.2x" % x, raw)))
        if arg is not None:
            message += " with argument %s" % format_hex(arg)
        return message

    def unknown_opcode(self, *args, **kw):
        return EmulatorError("Right before $%0.4x: %s\n" % (self.PC,
            self.error_message("Unknown", *args, **kw)))

    def not_implemented(self, raw=None, arg=None):
        return EmulatorError(self.error_message("Not implemented", raw, arg))

    def execute(self, opcode, length, cycles, flags, raw, arg=None):
        Z = None
        N = None
        H = None
        C = None

        # Order dependency: Check for prefix first
        if raw[0] == 0xcb: # PREFIX CB
            if opcode == 0x11: # RL C
                C = (self.C & (1<<7)) >> 7
                self.C = (self.C << 1) & 0xff
                self.C |= self.C_flag
                Z = (self.C == 0)
            elif opcode == 0x60: # BIT 4, B
                self.B = self.B | 0b00001000
                Z = (self.B & 1<<4) == 0
            elif opcode == 0x6b: # BIT 5, E
                Z = (self.E & 1<<5) == 0
            elif opcode == 0x7c: # BIT 7, H
                Z = (self.H & (1<<7)) == 0
            elif opcode == 0x21: # SLA C
                C = (self.C & (1<<7)) >> 7
                self.C <<= 1
                Z = self.C == 0
            elif opcode == 0x30: # SWAP B
                self.B = swap8(self.B)
                Z = (self.B == 0)
            elif opcode == 0x31: # SWAP C
                self.C = swap8(self.C)
                Z = (self.C == 0)
            elif opcode == 0x32: # SWAP D
                self.D = swap8(self.D)
                Z = (self.D == 0)
            elif opcode == 0x33: # SWAP E
                self.E = swap8(self.E)
                Z = (self.E == 0)
            elif opcode == 0x34: # SWAP H
                self.H = swap8(self.H)
                Z = (self.H == 0)
            elif opcode == 0x35: # SWAP L
                self.L = swap8(self.L)
                Z = (self.L == 0)
            elif opcode == 0x36: # SWAP (HL)
                value = swap8(self.memory[self.HL])
                self.memory[self.HL] = value
                Z = (value == 0)
            elif opcode == 0x37: # SWAP A
                self.A = swap8(self.A)
                Z = (self.A == 0)
            else:
                raise self.unknown_opcode(raw)
        elif raw[0] == 0x10:
            if opcode == 0x10: # STOP
                # Halt CPU/LCD display until button pressed
                raise self.not_implemented(raw, arg)
            else:
                raise self.unknown_opcode(raw)
        else:
            # Ordinary instructions
            if opcode == 0x00: # NOP
                pass
            elif opcode == 0x01: # LD BC, d16
                self.BC = arg
            elif opcode == 0x02: # LD (BC), A
                self.memory[self.BC] = self.A
            elif opcode == 0x03: # INC BC
                self.BC += 1
            elif opcode == 0x04: # INC B
                H = (self.B & 0x0f) == 0b1111
                self.B += 1
                Z = self.B == 0
            elif opcode == 0x05: # DEC B
                H = (self.B % 0xf) == 0b0000
                self.B -= 1
                Z = self.B == 0
                # TODO: Implement half-carry flag
            elif opcode == 0x06: # LD B, d8
                self.B = arg
            elif opcode == 0x07: # RLCA
                self.C_flag = (self.A & (1<<7)) >> 7
                self.A <<= 1
            elif opcode == 0x08: # LD (a16), SP
                self.memory.set16(arg, self.SP)
            elif opcode == 0x09: # ADD HL, BC
                n = self.HL + self.BC
                C = n > 0xffff
                self.HL = n
                # TODO: Set H
            elif opcode == 0x0a: # LD A, (BC)
                self.A = self.memory[self.BC]
            elif opcode == 0x0b: # DEC BC
                self.BC -= 1
            elif opcode == 0x0c: # INC C
                H = (self.C & 0x0f) == 0b1111
                self.C += 1
                Z = self.C == 0
            elif opcode == 0x0d: # DEC C
                H = (self.C % 0xf) == 0b0000
                self.C -= 1
                Z = self.C == 0
            elif opcode == 0x0e: # LD C, d8
                self.C = arg
            elif opcode == 0x0f: # RRCA
                C = (self.A & 0x1)
                self.A >>= 1
                self.A |= (self.C_flag << 7)
                Z = (self.A == 0)
            elif opcode == 0x10: # STOP
                # The fetch/decode should handle stop as a two-byte 0x10 0x00
                # instruction.
                raise EmulatorError("STOP")
            elif opcode == 0x11: # LD DE, d16
                self.DE = arg
            elif opcode == 0x12: # LD (DE), A
                self.memory[self.DE] = self.A
            elif opcode == 0x13: # INC DE
                self.DE += 1
            elif opcode == 0x14:  # INC D
                H = (self.D & 0xf) == 0b1111
                self.D += 1
                Z = self.D == 0
            elif opcode == 0x15: # DEC D
                H = (self.D % 0xf) == 0b0000
                self.D -= 1
                Z = self.D == 0
            elif opcode == 0x16: # LD D, d8
                self.D = arg
            elif opcode == 0x17: # RLA
                C = (self.A & (1<<7)) >> 7
                self.A <<= 1
                self.A |= self.C_flag
                Z = self.A == 0
            elif opcode == 0x18: # JR r8
                self.jmp(self.PC + arg)
            elif opcode == 0x19: # ADD HL, DE
                self.HL += self.DE
            elif opcode == 0x1a: # LD A, (DE)
                self.A = self.memory[self.DE]
            elif opcode == 0x1b: # RR E
                C = (self.E & 0x1)
                self.E >>= 1
                self.E |= self.C_flag << 7
                Z = (self.E == 0)
            elif opcode == 0x1c: # INC E
                H = (self.E & 0x0f) == 0b1111
                self.E += 1
                Z = self.E == 0
            elif opcode == 0x1d: # DEC E
                H = (self.E % 0xf) == 0b0000
                self.E -= 1
                Z = (self.E == 0)
            elif opcode == 0x1e: # LD E, d8
                self.E = arg
            elif opcode == 0x1f: # RRA
                C = (self.A & 0x1)
                self.A >>= 1
                self.A |= (self.C_flag << 7)
                Z = self.A == 0
            elif opcode == 0x20: # JR NZ, r8
                if not self.Z_flag:
                    cycles = cycles[0]
                    self.jmp(self.PC + arg)
                else:
                    cycles = cycles[1]
            elif opcode == 0x21: # LD HL, d16
                self.HL = arg
            elif opcode == 0x22: # LD (HL+), A
                self.memory[self.HL] = self.A
                self.HL += 1
            elif opcode == 0x23: # INC HL
                self.HL += 1
            elif opcode == 0x24: # INC H
                H = (self.H & 0x0f) == 0b1111
                self.H += 1
                Z = self.H == 0
            elif opcode == 0x25: # DEC H
                H = (self.H % 0xf) == 0b0000
                self.H -= 1
                Z = self.H == 0
            elif opcode == 0x26: # LD H, d8
                self.H = arg
            elif opcode == 0x27: # DAA
                # Set A to binary coded decimal (BCD)
                lo = self.A % 10
                hi = ((self.A - lo) % 100) // 10
                self.A = (hi << 4) | lo
            elif opcode == 0x28: # JR Z, r8
                if self.Z_flag:
                    cycles = cycles[0]
                    self.jmp(self.PC + arg)
                else:
                    cycles = cycles[1]
            elif opcode == 0x29: # ADD HL, HL
                n = self.HL + self.HL
                C = n > 0xffff
                self.HL = n
                # TODO: Set H
            elif opcode == 0x2a: # LD A, (HL+)
                self.A = self.memory[self.HL]
                self.HL = inc16(self.HL)
            elif opcode == 0x2b: # DEC HL
                self.HL -= 1
            elif opcode == 0x2c: # INC L
                H = (self.L & 0x0f) == 0b1111
                self.L += 1
                Z = self.L == 0
            elif opcode == 0x2d: # DEC L
                H = (self.L % 0xf) == 0b0000
                self.L -= 1
                Z = self.L == 0
            elif opcode == 0x2e: # LD L, d8
                self.L = arg
            elif opcode == 0x2f: # CPL
                self.A = ~self.A & 0xff
            elif opcode == 0x30: # JR NC, r8
                if not self.C_flag:
                    cycles = cycles[0]
                    self.jmp(self.PC + arg)
                else:
                    cycles = cycles[1]
            elif opcode == 0x31: # LD SP, d16
                self.SP = arg
            elif opcode == 0x32: # LD (HL-), A
                self.memory[self.HL] = self.A
                self.HL -= 1
            elif opcode == 0x33: # INC SP
                self.SP += 1
                Z = (self.SP == 0)
                # TODO: Set H flag
            elif opcode == 0x34: # INC (HL)
                n = self.memory[self.HL]
                H = (n & 0x0f) == 0b1111
                n = (n + 1) % 0x100
                self.memory[self.HL] = n
                Z = n == 0
            elif opcode == 0x35: # DEC (HL)
                n = self.memory[self.HL]
                H = (n % 0xf) == 0b0000
                n = (n - 1) % 0x100
                self.memory[self.HL] = n
                Z = n == 0
            elif opcode == 0x36: # LD (HL), d8
                self.memory[self.HL] = arg
            elif opcode == 0x37:  # SCF
                pass # flag is automatically set below
            elif opcode == 0x38: # JR C, r8
                if self.C_flag:
                    cycles = cycles[0]
                    self.jmp(self.PC + arg)
                else:
                    cycles = cycles[1]
            elif opcode == 0x39: # ADD HL, SP
                self.HL += self.SP
                # TODO: Set H and C
            elif opcode == 0x3a: # LD A, (HL-)
                self.A = self.memory[self.HL]
                self.HL -= 1
            elif opcode == 0x3b: # DEC SP
                self.SP -= 1
            elif opcode == 0x3c: # INC A
                H = (self.A & 0x0f) == 0b1111
                self.A += 1
                Z = (self.A == 0)
            elif opcode == 0x3d: # DEC A
                H = (self.A % 0xf) == 0b0000
                self.A -= 1
                Z = (self.A == 0)
            elif opcode == 0x3e: # LD A, d8
                self.A = arg
            elif opcode == 0x3f: # CCF
                self.C_flag = not self.C_flag
            elif opcode == 0x40:  # LD B, B
                pass # no op
            elif opcode == 0x41: # LD B, C
                self.B = self.C
            elif opcode == 0x42: # LD B, D
                self.B = self.D
            elif opcode == 0x43: # LD B, E
                self.B = self.E
            elif opcode == 0x44 : # LD B, H
                self.B = self.H
            elif opcode == 0x45: # LD B, L
                self.B = self.L
            elif opcode == 0x46: # LD B, (HL)
                self.B = self.memory[self.HL]
            elif opcode == 0x47: # LD B, A
                self.B = self.A
            elif opcode == 0x48: # LD C, B
                self.C == self.B
            elif opcode == 0x49: # LD C, C
                pass # no op
            elif opcode == 0x4a: # LD C, D
                self.C = self.D
            elif opcode == 0x4b: # LD C, E
                self.C = self.E
            elif opcode == 0x4c: # LD C, H
                self.C == self.H
            elif opcode == 0x4d: # LD C, L
                self.C = self.L
            elif opcode == 0x4e: # LD C, (HL)
                self.C = self.memory[self.HL]
            elif opcode == 0x4f: # LD C, A
                self.C = self.A
            elif opcode == 0x50: # LD D, B
                self.D = self.B
            elif opcode == 0x51: # LD D, C
                self.D = self.C
            elif opcode == 0x52: # LD D, D
                pass # no op
            elif opcode == 0x53: # LD D, E
                self.D = self.E
            elif opcode == 0x54: # LD D, H
                self.D = self.H
            elif opcode == 0x55: # LD D, L
                self.D = self.L
            elif opcode == 0x56: # LD D, (HL)
                self.D = self.memory[self.HL]
            elif opcode == 0x57: # LD D, A
                self.D = self.A
            elif opcode == 0x58: # LD E, B
                self.E = self.B
            elif opcode == 0x59: # LD E, C
                self.E = self.C
            elif opcode == 0x5a: # LD E, D
                self.E = self.D
            elif opcode == 0x5b: # LD E, E
                pass # no op
            elif opcode == 0x5c: # LD E, H
                self.E = self.H
            elif opcode == 0x5d: # LD E, L
                self.E = self.L
            elif opcode == 0x5e: # LD E, (HL)
                self.E = self.memory[self.HL]
            elif opcode == 0x5f: # LD E, A
                self.E = self.A
            elif opcode == 0x60: # LD H, B
                self.H = self.B
            elif opcode == 0x61: # LD H, C
                self.H = self.C
            elif opcode == 0x62: # LD H, D
                self.H = self.D
            elif opcode == 0x63: # LD H, E
                self.H = self.E
            elif opcode == 0x64: # LD H, H
                pass # no op
            elif opcode == 0x65: # LD H, L
                self.H = self.L
            elif opcode == 0x66: # LD H, (HL)
                self.H = self.memory[self.HL]
            elif opcode == 0x67: # LD H, A
                self.H = self.A
            elif opcode == 0x68: # LD L, B
                self.L = self.B
            elif opcode == 0x69: # LD L, C
                self.L = self.C
            elif opcode == 0x6a: # LD L, D
                self.L = self.D
            elif opcode == 0x6b: # LD L, E
                self.L = self.E
            elif opcode == 0x6c: # LD L, H
                self.L = self.H
            elif opcode == 0x6d: # LD L, L
                pass # no op
            elif opcode == 0x6e: # LD L, (HL)
                self.L = self.memory[self.HL]
            elif opcode == 0x6f: # LD L, A
                self.L = self.A
            elif opcode == 0x70: # LD (HL), B
                self.memory[self.HL] = self.B
            elif opcode == 0x71: # LD (HL), C
                self.memory[self.HL] = self.C
            elif opcode == 0x72: # LD (HL), D
                self.memory[self.HL] = self.D
            elif opcode == 0x73: # LD (HL), E
                self.memory[self.HL] = self.E
            elif opcode == 0x74: # LD (HL), H
                self.memory[self.HL] = self.H
            elif opcode == 0x75: # LD (HL), L
                self.memory[self.HL] = self.L
            elif opcode == 0x76: # HALT
                # Power down CPU until an interrupt occurs (for energy saving)
                raise self.not_implemented(raw, arg)
            elif opcode == 0x77: # LD (HL), A
                self.memory[self.HL] = self.A
            elif opcode == 0x78: # LD A, B
                self.A = self.B
            elif opcode == 0x79: # LD A, C
                self.A = self.C
            elif opcode == 0x7a: # LD A, B
                self.A = self.B
            elif opcode == 0x7b: # LD A, E
                self.A = self.E
            elif opcode == 0x7c: # LD A, H
                self.A = self.H
            elif opcode == 0x7d: # LD A, L
                self.A = self.L
            elif opcode == 0x7e: # LD A, (HL)
                self.A = self.memory[self.HL]
            elif opcode == 0x7f: # LD A, A
                pass # no op
            elif opcode == 0x80: # ADD A, B
                self.A += self.B
                Z = self.A == 0
                # TODO: Set H/C
            elif opcode == 0x81: # ADD A, C
                self.A += self.C
                Z = self.A == 0
                # TODO: Set H/C
            elif opcode == 0x82: # ADD A, D
                self.A += self.D
                Z = self.A == 0
                # TODO: Set H/C
            elif opcode == 0x83: # ADD A, E
                self.A += self.E
                Z = self.A == 0
                # TODO: Set H/C
            elif opcode == 0x84: # ADD A, H
                self.A += self.H
                Z = self.A == 0
                # TODO: Set H/C
            elif opcode == 0x85: # ADD A, L
                self.A += self.L
                Z = self.A == 0
                # TODO: Set H/C
            elif opcode == 0x86: # ADD A, (HL)
                self.A += self.memory[self.HL]
                Z = (self.A == 0)
                # TODO: Set other flags
            elif opcode == 0x87: # ADD A, A
                self.A += self.A
                Z = (self.A == 0)
                # TODO: Set other flags
            elif opcode == 0x88: # ADC A, B
                n = self.B + self.C_flag
                self.A += n
                Z = (self.A == 0)
                # TODO: Carry stuff
            elif opcode == 0x89: # ADC A, C
                n = self.C + self.C_flag
                self.A += n
                Z = (self.A == 0)
                # TODO: Carry stuff
            elif opcode == 0x8a: # ADC A, D
                n = self.D + self.C_flag
                self.A += n
                Z = (self.A == 0)
                # TODO: Carry stuff
            elif opcode == 0x8b: # ADC A, E
                n = self.D + self.C_flag
                self.A += n
                Z = (self.A == 0)
                # TODO: Carry stuff
            elif opcode == 0x8c: # ADC A, H
                n = self.H + self.C_flag
                self.A += n
                Z = (self.A == 0)
                # TODO: Carry stuff
            elif opcode == 0x8d: # ADC A, L
                n = self.H + self.C_flag
                self.A += n
                Z = (self.A == 0)
                # TODO: Carry stuff
            elif opcode == 0x8e: # ADC A, (HL)
                n = self.memory[self.HL] + self.C_flag
                self.A += n
                Z = (self.A == 0)
                # TODO: Carry stuff
            elif opcode == 0x8f: # ADC A, A
                n = self.memory[self.HL] + self.C_flag
                self.A += n
                Z = (self.A == 0)
                # TODO: Carry stuff
            elif opcode == 0x90: # SUB B
                self.A = (self.A - self.B) % 0x100
                Z = (self.A == 0)
                # TODO: set half carry and carry flags
            elif opcode == 0x91: # SUB C
                self.A -= self.C
                Z = (self.A == 0)
                # TODO: set half carry and carry flags
            elif opcode == 0x92: # SUB D
                self.A -= self.D
                Z = (self.A == 0)
                # TODO: set half carry and carry flags
            elif opcode == 0x93: # SUB E
                self.A -= self.E
                Z = (self.A == 0)
                # TODO: set half carry and carry flags
            elif opcode == 0x94: # SUB H
                self.A -= self.H
                Z = (self.A == 0)
                # TODO: set half carry and carry flags
            elif opcode == 0x95: # SUB L
                self.A -= self.L
                Z = (self.A == 0)
                # TODO: set half carry and carry flags
            elif opcode == 0x96: # SUB (HL)
                self.A -= self.memory[self.HL]
                Z = (self.A == 0)
                # TODO: set half carry and carry flags
            elif opcode == 0x97: # SUB A
                self.A -= self.A
                self.A = (self.A - self.A) % 0x100
                Z = (self.A == 0)
                # TODO: set half carry and carry flags
            elif opcode == 0x98: # SBC A, B
                n = self.B + self.C_flag
                self.A -= n
                Z = self.A == 0
                # TODO H/C flags
            elif opcode == 0x99: # SBC A, C
                n = self.C + self.C_flag
                self.A -= n
                Z = self.A == 0
                # TODO H/C flags
            elif opcode == 0x9a: # SBC A, D
                n = self.D + self.C_flag
                self.A -= n
                Z = self.A == 0
                # TODO H/C flags
            elif opcode == 0x9b: # SBC A, E
                n = self.E + self.C_flag
                self.A -= n
                Z = self.A == 0
                # TODO H/C flags
            elif opcode == 0x9c: # SBC A, H
                n = self.H + self.C_flag
                self.A -= n
                Z = self.A == 0
                # TODO H/C flags
            elif opcode == 0x9d: # SBC A, L
                n = self.L + self.C_flag
                self.A -= n
                Z = self.A == 0
                # TODO H/C flags
            elif opcode == 0x9e: # SBC A, (HL)
                n = self.memory[self.HL] + self.C_flag
                self.A -= n
                Z = self.A == 0
                # TODO H/C flags
            elif opcode == 0x9f: # SBC A, A
                n = self.A + self.C_flag
                self.A -= n
                Z = self.A == 0
                # TODO H/C flags
            elif opcode == 0xa0: # AND B
                self.A &= self.B
                Z = self.A == 0
            elif opcode == 0xa1: # AND C
                self.A &= self.C
                Z = self.A == 0
            elif opcode == 0xa2: # AND D
                self.A &= self.D
                Z = self.A == 0
            elif opcode == 0xa3: # AND E
                self.A &= self.E
                Z = self.A == 0
            elif opcode == 0xa4: # AND H
                self.A &= self.H
                Z = self.A == 0
            elif opcode == 0xa5: # AND L
                self.A &= self.L
                Z = self.A == 0
            elif opcode == 0xa6: # AND (HL)
                self.A &= self.memory[self.HL]
                Z = self.A == 0
            elif opcode == 0xa7: # AND A
                # A & A = A
                Z = self.A == 0
            elif opcode == 0xa8: # XOR B
                self.A ^= self.B
                Z = self.A == 0
            elif opcode == 0xa9: # XOR C
                self.A ^= self.C
                Z = self.A == 0
            elif opcode == 0xaa: # XOR D
                self.A ^= self.D
                Z = self.A == 0
            elif opcode == 0xab: # XOR E
                self.A ^= self.E
                Z = self.A == 0
            elif opcode == 0xac: # XOR H
                self.A ^= self.H
                Z = self.A == 0
            elif opcode == 0xad: # XOR L
                self.A ^= self.L
                Z = self.A == 0
            elif opcode == 0xae: # XOR (HL)
                self.A ^= self.memory[self.HL]
                Z = self.A == 0
            elif opcode == 0xaf: # XOR A
                self.A = 0
                Z = True
            elif opcode == 0xb0: # OR B
                self.A |= self.B
                Z = self.A == 0
            elif opcode == 0xb1: # OR C
                self.A |= self.C
                Z = self.A == 0
            elif opcode == 0xb2: # OR D
                self.A |= self.D
                Z = self.A == 0
            elif opcode == 0xb3: # OR E
                self.A |= self.E
                Z = self.A == 0
            elif opcode == 0xb4: # OR H
                self.A |= self.H
                Z = self.A == 0
            elif opcode == 0xb5: # OR L
                self.A |= self.L
                Z = self.A == 0
            elif opcode == 0xb6: # OR (HL)
                self.A |= self.memory[self.HL]
                Z = self.A == 0
            elif opcode == 0xb7: # OR A
                self.A |= self.A # NOTE: No-op statement really
                Z = self.A == 0
            elif opcode == 0xb8: # CP B
                result = (self.A - self.B) % 0x100
                Z = (result == 0)
                C = (self.A < result)
                # TODO: set H
            elif opcode == 0xb9: # CP C
                result = (self.A - self.C) % 0x100
                Z = (result == 0)
                C = (self.A < result)
                # TODO: set H
            elif opcode == 0xba: # CP D
                result = (self.A - self.D) % 0x100
                Z = (result == 0)
                C = (self.A < result)
                # TODO: set H
            elif opcode == 0xbb: # CP E
                result = (self.A - self.E) % 0x100
                Z = (result == 0)
                C = (self.A < result)
                # TODO: set H
            elif opcode == 0xbc: # CP H
                result = (self.A - self.H) % 0x100
                Z = (result == 0)
                C = (self.A < result)
                # TODO: set H
            elif opcode == 0xbd: # CP L
                result = (self.A - self.L) % 0x100
                Z = (result == 0)
                C = (self.A < result)
                # TODO: set H
            elif opcode == 0xbe: # CP (HL)
                result = (self.A - self.memory[self.HL]) % 0x100
                Z = (result == 0)
                C = (self.A < result)
                # TODO: set H
            elif opcode == 0xbf: # CP A
                result = (self.A - self.A) % 0x100
                Z = (result == 0)
                C = (self.A < result)
                # TODO: set H
            elif opcode == 0xc0: # RET NZ
                if not self.Z_flag:
                    cycles = cycles[1]
                    self.ret()
                else:
                    cycles = cycles[0]
            elif opcode == 0xc1: # POP BC
                self.BC = self.pop()
            elif opcode == 0xc2: # JP NZ, a16
                if not self.Z_flag:
                    cycles = cycles[0]
                    self.jmp(arg)
                else:
                    cycles = cycles[1]
            elif opcode == 0xc3: # JP a16
                self.jmp(arg)
            elif opcode == 0xc4: # CALL NZ, a16
                if not self.Z_flag:
                    cycles = cycles[0]
                    self.call(arg)
                else:
                    cycles = cycles[1]
            elif opcode == 0xc5: # PUSH BC
                self.push(self.BC)
            elif opcode == 0xc6: # ADD A, d8
                self.A += arg
                Z = self.A == 0
                # TODO: Set H/C
            elif opcode == 0xc7: # RST 00H
                self.rst(0x00)
            elif opcode == 0xc8: # RET Z
                if self.Z_flag:
                    cycles = cycles[0]
                    self.ret()
                else:
                    cycles = cycles[1]
            elif opcode == 0xc9: # RET
                self.ret()
            elif opcode == 0xca: # JP Z, a16
                if self.Z_flag:
                    cycles = cycles[0]
                    self.jmp(arg)
                else:
                    cycles = cycles[1]
            elif opcode == 0xcb: # PREFIX CB
                raise InvalidOpcodeError("Invalid opcode 0x%0.2x at $%0.4x" %
                        (opcode, self.PC - length))
            elif opcode == 0xcc: # CALL Z, a16
                if self.Z_flag:
                    cycles = cycles[0]
                    self.call(arg)
                else:
                    cycles = cycles[1]
            elif opcode == 0xcd: # CALL a16
                self.call(arg)
            elif opcode == 0xce: # ADC A, d8
                n = arg + self.C_flag
                self.A += n
                Z = self.A == 0
                # TODO: Set C, H
            elif opcode == 0xcf: # RST 08H
                self.rst(0x08)
            elif opcode == 0xd0: # RET NC
                if not self.C_flag:
                    cycles = cycles[0]
                    self.ret()
                else:
                    cycles = cycles[1]
            elif opcode == 0xd1: # POP DE
                self.DE = self.pop()
            elif opcode == 0xd2: # JP NC, a16
                if not self.C_flag:
                    cycles = cycles[0]
                    self.jmp(arg)
                else:
                    cycles = cycles[1]
            elif opcode == 0xd3: # -
                raise InvalidOpcodeError("Invalid opcode 0x%0.2x at $%0.4x" %
                        (opcode, self.PC - length))
            elif opcode == 0xd4: # CALL NC, a16
                if not self.C_flag:
                    cycles = cycles[0]
                    self.call(arg)
                else:
                    cycles = cycles[1]
            elif opcode == 0xd5: # PUSH DE
                self.push(self.DE)
            elif opcode == 0xd6: # SUB d8
                self.A -= arg
                Z = (self.A == 0)
                # TODO: set half carry and carry flags
            elif opcode == 0xd7: # RST 10H
                self.rst(0x10)
            elif opcode == 0xd8: # RET C
                if self.C_flag:
                    cycles = cycles[0]
                    self.ret()
                else:
                    cycles = cycles[1]
            elif opcode == 0xd9: # RETI
                self.ret()
                self.IME = True
            elif opcode == 0xda: # JP C, a16
                if self.C_flag:
                    cycles = cycles[0]
                    self.jmp(arg)
                else:
                    cycles = cycles[1]
            elif opcode == 0xdb: # -
                raise InvalidOpcodeError("Invalid opcode 0x%0.2x at $%0.4x" %
                        (opcode, self.PC - length))
            elif opcode == 0xdc: # CALL C
                if self.C_flag:
                    cycles = cycles[0]
                    self.call(self.C)
                else:
                    cycles = cycles[1]
            elif opcode == 0xdd: # -
                raise InvalidOpcodeError("Invalid opcode 0x%0.2x at $%0.4x" %
                        (opcode, self.PC - length))
            elif opcode == 0xde: # SBC A, d8
                n = arg + self.C_flag
                self.A -= n
                Z = self.A == 0
                # TODO H/C flags
            elif opcode == 0xdf: # RST 18H
                self.rst(0x18)
            elif opcode == 0xe0: # LDH ($ff00+a8), A
                self.memory[arg] = self.A
            elif opcode == 0xe1: # POP HL
                self.HL = self.pop()
            elif opcode == 0xe2: # LD ($ff00+C), A
                self.memory[(0xff00 + self.C) % 0x10000] = self.A
            elif opcode == 0xe3: # -
                raise InvalidOpcodeError("Invalid opcode 0x%0.2x at $%0.4x" %
                        (opcode, self.PC - length))
            elif opcode == 0xe4: # -
                raise InvalidOpcodeError("Invalid opcode 0x%0.2x at $%0.4x" %
                        (opcode, self.PC - length))
            elif opcode == 0xe5: # PUSH HL
                self.push(self.HL)
            elif opcode == 0xe6: # AND d8
                self.A &= arg
                Z = self.A == 0
            elif opcode == 0xe7: # RST 20H
                self.rst(0x20)
            elif opcode == 0xe8: # ADD SP, r8
                self.SP += arg
                # TODO: Set H/C
            elif opcode == 0xe9: # JP (HL)
                self.jmp(self.memory[self.HL])
            elif opcode == 0xea: # LD (a16), A
                self.memory[arg] = self.A
            elif opcode == 0xeb: # -
                raise InvalidOpcodeError("Invalid opcode 0x%0.2x at $%0.4x" %
                        (opcode, self.PC - length))
            elif opcode == 0xec: # -
                raise InvalidOpcodeError("Invalid opcode 0x%0.2x at $%0.4x" %
                        (opcode, self.PC - length))
            elif opcode == 0xed: # -
                raise InvalidOpcodeError("Invalid opcode 0x%0.2x at $%0.4x" %
                        (opcode, self.PC - length))
            elif opcode == 0xee: # XOR d8
                self.A ^= arg
                Z = self.A == 0
            elif opcode == 0xef: # RST 28H
                self.rst(0x28)
            elif opcode == 0xf0: # LDH A, (a8)
                self.A = self.memory[arg]
            elif opcode == 0xf1: # POP AF
                self.AF = self.pop()
                # According to official manual, no flags should be set here
                # Once again, the Pastraiser seem to have errors.
            elif opcode == 0xf2: # LD A, (C)
                self.A = self.memory[self.C]
            elif opcode == 0xf3: # DI
                self.IME = False
            elif opcode == 0xf4: # -
                raise InvalidOpcodeError("Invalid opcode 0x%0.2x at $%0.4x" %
                        (opcode, self.PC - length))
            elif opcode == 0xf5: # PUSH AF
                self.push(self.AF)
            elif opcode == 0xf6: # OR d8
                self.A |= arg
                Z = self.A == 0
            elif opcode == 0xf7: # RST 30H
                self.rst(0x30)
            elif opcode == 0xf8: # LD HL, SP+r8
                self.HL = self.SP + arg
                # TODO: Set H/C
            elif opcode == 0xf9: # LD SP, HL
                self.SP = self.HL
            elif opcode == 0xfa: # LD A, (a16)
                self.A = self.memory[arg]
            elif opcode == 0xfb: # EI
                self.IME = True
            elif opcode == 0xfc: # -
                raise InvalidOpcodeError("Invalid opcode 0x%0.2x at $%0.4x" %
                        (opcode, self.PC - length))
            elif opcode == 0xfd: # -
                raise InvalidOpcodeError("Invalid opcode 0x%0.2x at $%0.4x" %
                        (opcode, self.PC - length))
            elif opcode == 0xfe: # CP d8
                result = (self.A - arg) % 0x100
                Z = (result == 0)
                C = (self.A < arg)
                # TODO: set H
            elif opcode == 0xff: # RST 38H
                self.rst(0x38)
            else:
                raise self.unknown_opcode(raw)

        # Update flags after executing the instruction
        if flags is not None:
            for shift, flag in zip((7, 6, 5, 4), flags):
                if flag == 0:
                    self.F &= ~(1 << shift)
                elif flag == 1:
                    self.F |= 1<<shift
                elif flag == "Z" and Z is not None:
                    self.Z_flag = Z
                elif flag == "H" and H is not None:
                    self.H_flag = H
                elif flag == "N" and N is not None:
                    self.N_flag = N
                elif flag == "C" and C is not None:
                    self.C_flag = C

        self.cycles += cycles
        self.total_cycles += cycles
