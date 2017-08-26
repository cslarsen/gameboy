import sys

from util import (
    format_bin,
    format_hex,
    u8_to_signed,
)

from opcodes import (
    add_0xff00_opcodes,
    extended_opcodes,
    opcodes,
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
        self.pc = 0 # and not 0x100, because we have a boot ROM
        self.sp = 0

        # Amount of cycles spent
        self.cycles = 0

        # Save last fully decoded instruction for errors
        self.prev_inst = ""

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
        name, bytelen, cycles, flags = opcodes[opcode]
        raw = [opcode]

        if opcode == 0xcb: # PREFIX CB
            # Fetch the next instruction as well
            self.pc += bytelen
            opcode = self.fetch()
            raw.append(opcode)

            name, bytelen, xcycles, flags = extended_opcodes[opcode]
            cycles += xcycles

        # Decode arguments
        arg = None
        if bytelen > 1:
            arg = 0
            for offset in range(1, bytelen):
                byte = self.memory[self.pc + offset]
                raw.append(byte)
                arg |= byte << 8*(offset-1)

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
                arg = u8_to_signed(arg)
                abs_addr = self.pc + bytelen + arg
                if arg < 0:
                    name = name.replace("r8", "PC-$%0.4x (@$%0.4x)" % (-arg,
                        abs_addr))
                else:
                    name = name.replace("r8", "PC+$%0.4x (@$%0.4x)" % (arg,
                        abs_addr))
            else:
                raise RuntimeError(
                    "Opcode 0x%0.2x %r has unspecified argument: %s" %
                        (opcode, name, format_hex(arg)))

        # TODO: Handle extended opcodes

        self.pc += bytelen
        return name, opcode, bytelen, cycles, flags, arg, raw

    def run(self, trace=False):
        while True:
            self.step(trace)

    def step(self, trace=False):
        address = self.pc
        opcode = self.fetch()
        name, opcode, length, cycles, flags, arg, raw = self.decode(opcode)

        self.prev_inst = "$%0.4x:" % address
        self.prev_inst += "  %-20s" % " ".join(map(lambda x: "0x%0.2x" % x,
            raw))
        self.prev_inst += "  %-20s" % name

        if trace:
            sys.stdout.write(self.prev_inst)

        self.execute(opcode, length, cycles, flags, raw, arg)

        if trace and flags is not None:
            sys.stdout.write("\n        implicit flags: %s" % " ".join(flags))

        if trace:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self.print_registers()

    def print_registers(self):
        print("        pc=$%0.4x sp=$%0.4x a=$%x b=$%x c=$%x d=$%x e=$%x f=$%x h=$%x l=$%x" %
                (self.pc, self.sp, self.A, self.B, self.C, self.D, self.E,
                    self.F, self.H, self.L))
        print("        flags=%s cycles=%d" % (format_bin(self.F), self.cycles))

    @property
    def HL(self):
        return self.H << 8 | self.L

    @HL.setter
    def HL(self, value):
        assert(0 <= value <= 0xffff)
        self.H = (value & 0xff00) >> 8
        self.L = value & 0xff

    @property
    def z_flagged(self):
        return self.F & (1<<6) != 0

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
            return RuntimeError("%s\n%s" % (error_message("Unknown"),
                self.prev_inst))

        def not_implemented():
            return NotImplementedError(error_message("Not implemented"))

        # Order dependency: Check for prefix first
        if raw[0] == 0xcb: # PREFIX CB
            if opcode == 0x11: # RL C
                raise not_implemented()
            elif opcode == 0x7c: # BIT 7, H
                zero = (self.H & (1<<6) == 0)
            else:
                raise unknown_opcode()
        else:
            if opcode == 0x00: # NOP
                pass
            elif opcode == 0x31: # LD SP, d16
                self.sp = arg
            elif opcode == 0xaf: # XOR A
                self.A = 0
                zero = True
            elif opcode == 0x21: # LD HL, d16
                self.HL = arg
            elif opcode == 0x32: # LD (HL-), A
                self.memory[self.HL] = self.A
                self.HL -= 1
            elif opcode == 0x20: # JR NZ, r8
                if not self.z_flagged:
                    cycles = cycles[0]
                    self.pc += arg # performs jump
                else:
                    cycles = cycles[1]
            else:
                raise unknown_opcode()

        # Update flags after executing the instruction
        if flags is not None:
            for shift, flag in zip((6, 5, 4, 3), flags):
                if flag == "0":
                    self.F &= ~(1 << shift)
                elif flag == "1":
                    self.F ^= 1<<shift
                elif flag == "Z" and zero:
                    self.F ^= 1<<shift
                elif flag == "H" and half_carry:
                    self.F ^= 1<<shift
                elif flag == "N" and subtract:
                    self.F ^= 1<<shift
                elif flag == "C" and carry:
                    self.F ^= 1<<shift

        self.cycles += cycles
