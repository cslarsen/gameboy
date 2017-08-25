import sys
from opcodes import opcodes, extended_opcodes, add_0xff00_opcodes

from __init__ import (
    format_hex,
    unsigned8_to_signed,
)

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
