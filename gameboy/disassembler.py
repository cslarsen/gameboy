import sys

from opcodes import (
    add_0xff00_opcodes,
    extended_opcodes,
    opcodes,
    TYPE_A16,
    TYPE_A8,
    TYPE_D16,
    TYPE_D8,
    TYPE_R8,
    TYPE_VOID,
)

from __init__ import (
    format_hex,
    u8_to_signed,
)

def disassemble(code, start_address=0x0000, length=None, stream=sys.stdout):
    """Disassembles binary code."""
    write = stream.write
    index = 0

    if length is None:
        length = len(code)

    # Whether the previous instruciton was the 0xcb prefix opcode
    prefix = False

    while index < length:
        try:
            address = start_address + index
            opcode = code[index]
            table = opcodes if not prefix else extended_opcodes
            name, bytelen, type, cycles, flags = table[opcode]
        except KeyError as e:
            raise KeyError("Unknown %sopcode 0x%0.2x" % (
                "prefixed " if prefix else "", int(str(e))))

        if not prefix:
            write("$%0.4x:  " % address)
            raw = ""

        for i in range(index, index + bytelen):
            raw += "0x%0.2x " % code[i]

        arg = 0
        for offset in range(1, bytelen):
            arg |= code[index + offset] << 8*(offset-1)

        instruction = ""
        if bytelen > 1:
            if type == TYPE_VOID:
                pass
            elif type == TYPE_D8:
                name = name.replace("d8", format_hex(arg))
            elif type == TYPE_D16:
                name = name.replace("d16", format_hex(arg))
            elif type == TYPE_A8:
                if opcode in add_0xff00_opcodes:
                    name = name.replace("a8", "$ff00+$%0.2x" % arg)
                    arg += 0xff00
                else:
                    name = name.replace("a8", format_hex(arg))
            elif type == TYPE_A16:
                name = name.replace("a16", "$%0.4x" % arg)
            elif type == TYPE_R8:
                arg = u8_to_signed(arg)
                abs_addr = address + bytelen + arg
                if arg < 0:
                    name = name.replace("r8", "PC-$%0.2x ($%0.4x)" % (-arg,
                        abs_addr))
                else:
                    name = name.replace("r8", "PC+$%0.2x ($%0.4x)" %
                            (arg, abs_addr))
            else:
                raise RuntimeError(
                    "Unexpected argument for opcode 0x%0.2x %r: %s" % (opcode,
                        name, format_hex(arg)))

        if opcode != 0xcb:
            write("%-20s " % raw)
            instruction = name + instruction
            write("%-24s" % instruction)

            if flags is not None:
                for flag in flags:
                    assert(flag in ("Z", "N", "H", "C", "0", "1"))
                write(" flags %s" % " ".join(flags))

            prefix = False
            write("\n")
        else:
            prefix = True

        index += bytelen
