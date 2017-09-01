"""
Contains opcodes for the 8-bit Sharp LR35902 CPU running at 4.19 MHz. This CPU
is similar to the Zilog Z80 and Intel 8080 CPUs.

The mnemonics follow http://pastraiser.com/cpu/gameboy/gameboy_opcodes.html

NOTE: The above link says that 0xe2 takes one 8-bit argument, but it doesn't:
https://stackoverflow.com/a/41422692/21028
"""

# Instruction argument types
TYPE_VOID = 0
TYPE_D8 = 1
TYPE_D16 = 2
TYPE_A8 = 3
TYPE_A16 = 4
TYPE_R8 = 5

# Opcodes whose argument should be added with 0xff00
add_0xff00_opcodes = (0xe0, 0xf0)

# Extended opcodes. Use this table after the opcode 0xcb has been encountered
# from the preceding table. BYte lengths here are EXCLUSIVE the preceding
# prefix opcode.
extended_opcodes = {
    0x11: ("RL C",            1, TYPE_VOID,   8, ("Z", "0", "0", "C")),
    0x7c: ("BIT 7, H",        1, TYPE_VOID,   8, ("Z", "0", "1")),
}

# Maps raw byte to (label, byte length, argument type, cycles or (cycles for
# taken branch, cycles for not taken branch), flags).
opcodes = {
    # RAW BYTE, LABEL, LENGTH, ARGUMENT TYPE, CYCLES, FLAGS
    0x00: ("NOP",             1, TYPE_VOID,  4, None),
    0x01: ("LD BC, d16",      3, TYPE_D16,  12, None),
    0x02: ("LD (BC), A",      1, TYPE_VOID,  8, None),
    0x03: ("INC BC",          1, TYPE_VOID,  8, None),
    0x04: ("INC B",           1, TYPE_VOID,  4, ("Z", "0", "H")),
    0x05: ("DEC B",           1, TYPE_VOID,  4, ("Z", "1", "H")),
    0x06: ("LD B, d8",        2, TYPE_D8,    8, None),
    0x08: ("LD (a16), SP",    3, TYPE_A16,  20, None),
    0x0b: ("DEC BC",          1, TYPE_VOID,  8, None),
    0x0c: ("INC C",           1, TYPE_VOID,  4, ("Z", "0", "H")),
    0x0d: ("DEC C",           1, TYPE_VOID,  4, ("Z", "1", "H")),
    0x0e: ("LD C, d8",        2, TYPE_D8,    8, None),
    0x10: ("STOP",            2, TYPE_VOID,  4, None),
    0x11: ("LD DE, d16",      3, TYPE_D16,  12, None),
    0x13: ("INC DE",          1, TYPE_VOID,  8, None),
    0x15: ("DEC D",           1, TYPE_VOID,  4, ("Z", "1", "H")),
    0x16: ("LD D, d8",        2, TYPE_D8,    8, None),
    0x17: ("RLA",             1, TYPE_VOID,  4, None),
    0x18: ("JR r8",           2, TYPE_R8,   12, None),
    0x1a: ("LD A, (DE)",      1, TYPE_VOID, 18, None),
    0x1d: ("DEC E",           1, TYPE_VOID,  4, ("Z", "1", "H")),
    0x1e: ("LD E, d8",        2, TYPE_D8,    8, None),
    0x20: ("JR NZ, r8",       2, TYPE_R8,  (12, 8), None),
    0x21: ("LD HL, d16",      3, TYPE_D16,  12, None),
    0x22: ("LD (HL+), A",     1, TYPE_VOID,  8, None),
    0x23: ("INC HL",          1, TYPE_VOID,  8, None),
    0x24: ("INC H",           1, TYPE_VOID,  4, ("Z", "0", "H")),
    0x28: ("JR Z, r8",        2, TYPE_VOID, (12, 8), None),
    0x2e: ("LD L, d8",        2, TYPE_D8,    8, None),
    0x31: ("LD SP, d16",      3, TYPE_D16,  12, None),
    0x32: ("LD (HL-), A",     1, TYPE_VOID,  8, None),
    0x33: ("INC SP",          1, TYPE_VOID,  8, None),
    0x3c: ("INC A",           1, TYPE_VOID,  4, ("Z", "0", "H")),
    0x3d: ("DEC A",           1, TYPE_VOID,  4, ("Z", "1", "H")),
    0x3e: ("LD A, d8",        2, TYPE_D8,    8, None),
    0x42: ("LD B, D",         1, TYPE_VOID,  4, None),
    0x4f: ("LD C, A",         1, TYPE_VOID,  4, None),
    0x57: ("LD D, A",         1, TYPE_VOID,  4, None),
    0x63: ("LD H, E",         1, TYPE_VOID,  4, None),
    0x66: ("LD H, (HL)",      1, TYPE_VOID,  8, None),
    0x67: ("LD H, A",         1, TYPE_VOID,  4, None),
    0x6e: ("LD L, (HL)",      1, TYPE_VOID,  8, None),
    0x73: ("LD (HL), E",      1, TYPE_VOID,  8, None),
    0x76: ("HALT",            1, TYPE_VOID,  4, None),
    0x77: ("LD (HL), A",      1, TYPE_VOID,  8, None),
    0x78: ("LD A, B",         1, TYPE_VOID,  4, None),
    0x7b: ("LD A, E",         1, TYPE_VOID,  4, None),
    0x7c: ("LD A, H",         1, TYPE_VOID,  4, None),
    0x7d: ("LD A, L",         1, TYPE_VOID,  4, None),
    0x83: ("ADD A, E",        1, TYPE_VOID,  4, ("Z", "0", "H", "C")),
    0x86: ("ADD A, (HL)",     1, TYPE_VOID,  8, ("Z", "0", "H", "C")),
    0x88: ("ADC A, B",        1, TYPE_VOID,  4, ("Z", "0", "H", "C")),
    0x89: ("ADC A, C",        1, TYPE_VOID,  4, ("Z", "0", "H", "C")),
    0x90: ("SUB B",           1, TYPE_VOID,  4, ("Z", "1", "H", "C")),
    0x99: ("SBC A, C",        1, TYPE_VOID,  4, ("Z", "1", "H", "C")),
    0x9f: ("SBC A, A",        1, TYPE_VOID,  4, ("Z", "1", "H", "C")),
    0xa5: ("AND L",           1, TYPE_VOID,  4, ("Z", "0", "1", "0")),
    0xaf: ("XOR A",           1, TYPE_VOID,  4, ("Z", "0", "0", "0")),
    0xb9: ("CP C",            1, TYPE_VOID,  4, ("Z", "1", "H", "C")),
    0xbb: ("CP E",            1, TYPE_VOID,  4, ("Z", "1", "H", "C")),
    0xbe: ("CP (HL)",         1, TYPE_VOID,  8, ("Z", "1", "H", "C")),
    0xc1: ("POP BC",          1, TYPE_VOID,  12, None),
    0xc3: ("JP a16",          3, TYPE_A16,   16, None),
    0xc5: ("PUSH BC",         1, TYPE_VOID,  16, None),
    0xc9: ("RET",             1, TYPE_VOID,  16, None),
    0xcb: ("PREFIX CB",       1, TYPE_VOID,   4, None),
    0xcc: ("CALL Z, a16",     3, TYPE_A16,  (24, 12), None),
    0xcd: ("CALL a16",        3, TYPE_A16,   24, None),
    0xce: ("ADD A, d8",       2, TYPE_D8,     8, ("Z", "0", "H", "C")),
    0xd9: ("RETI",            1, TYPE_VOID,  16, None),
    0xdd: ("-",               1, TYPE_VOID,   0, None), # Invalid instruciton for .DB
    0xe0: ("LD (a8), A",      2, TYPE_A8,    12, None), # NOTE: Some say LDH
    0xe2: ("LD ($ff00+C), A", 1, TYPE_VOID,   8, None),
    0xea: ("LD (a16), A",     3, TYPE_A16,   16, None),
    0xf0: ("LDH A, (a8)",     2, TYPE_A8,    12, None),
    0xf3: ("DI",              1, TYPE_VOID,   4, None),
    0xf7: ("RST 30H",         1, TYPE_VOID,  16, None),
    0xf9: ("LD SP, HL",       1, TYPE_VOID,   8, None), # NOTE: Nintendo manual says 2 cycles?
    0xfa: ("LD A, (a16)",     3, TYPE_A16,   16, None),
    0xfb: ("EI",              1, TYPE_VOID,   4, None),
    0xfe: ("CP d8",           2, TYPE_D8,     8, ("Z", "1", "H", "C")),
    0xff: ("RST 38H",         1, TYPE_VOID,  16, None),
}
