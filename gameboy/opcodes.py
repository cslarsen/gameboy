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
prefix_opcodes = (0xcb, 0x10)

# Extended opcodes. Use this table after the opcode 0xcb has been encountered
# from the preceding table. BYte lengths here are EXCLUSIVE the preceding
# prefix opcode.
extended_opcodes = {
    0x11: ("RL C",            1, TYPE_VOID,   8, ("Z", 0, 0, "C")),
    0x30: ("SWAP B",          2, TYPE_VOID,   8, ("Z", 0, 0, 0)),
    0x31: ("SWAP C",          2, TYPE_VOID,   8, ("Z", 0, 0, 0)),
    0x32: ("SWAP D",          2, TYPE_VOID,   8, ("Z", 0, 0, 0)),
    0x33: ("SWAP E",          2, TYPE_VOID,   8, ("Z", 0, 0, 0)),
    0x34: ("SWAP H",          2, TYPE_VOID,   8, ("Z", 0, 0, 0)),
    0x35: ("SWAP L",          2, TYPE_VOID,   8, ("Z", 0, 0, 0)),
    0x36: ("SWAP (HL)",       2, TYPE_VOID,   8, ("Z", 0, 0, 0)),
    0x37: ("SWAP A",          2, TYPE_VOID,   8, ("Z", 0, 0, 0)),
    0x7c: ("BIT 7, H",        1, TYPE_VOID,   8, ("Z", 0, 1)),
}

# Maps raw byte to (label, byte length, argument type, cycles or (cycles for
# taken branch, cycles for not taken branch), flags).
opcodes = {
    # RAW BYTE, LABEL, LENGTH, ARGUMENT TYPE, CYCLES, FLAGS
    0x00: ("NOP",             1, TYPE_VOID,  4, None),
    0x01: ("LD BC, d16",      3, TYPE_D16,  12, None),
    0x02: ("LD (BC), A",      1, TYPE_VOID,  8, None),
    0x03: ("INC BC",          1, TYPE_VOID,  8, None),
    0x04: ("INC B",           1, TYPE_VOID,  4, ("Z", 0, "H")),
    0x05: ("DEC B",           1, TYPE_VOID,  4, ("Z", 1, "H")),
    0x06: ("LD B, d8",        2, TYPE_D8,    8, None),
    0x07: ("RLCA",            1, TYPE_VOID,  4, (0, 0, 0, "C")),
    0x08: ("LD (a16), SP",    3, TYPE_A16,  20, None),
    0x09: ("ADD HL, BC",      1, TYPE_VOID,  8, (None, 0, "H", "C")),
    0x0a: ("LD A, (BC)",      1, TYPE_VOID,  8, None),
    0x0b: ("DEC BC",          1, TYPE_VOID,  8, None),
    0x0c: ("INC C",           1, TYPE_VOID,  4, ("Z", 0, "H")),
    0x0d: ("DEC C",           1, TYPE_VOID,  4, ("Z", 1, "H")),
    0x0e: ("LD C, d8",        2, TYPE_D8,    8, None),
    0x0f: ("RRCA",            1, TYPE_VOID,  4, (0, 0, 0, "C")),
    0x10: ("STOP",            2, TYPE_VOID,  4, None),
    0x11: ("LD DE, d16",      3, TYPE_D16,  12, None),
    0x12: ("LD (DE), A",      1, TYPE_VOID,  8, None),
    0x13: ("INC DE",          1, TYPE_VOID,  8, None),
    0x14: ("INC D",           1, TYPE_VOID,  4, ("Z", 0, "H")),
    0x15: ("DEC D",           1, TYPE_VOID,  4, ("Z", 1, "H")),
    0x16: ("LD D, d8",        2, TYPE_D8,    8, None),
    0x17: ("RLA",             1, TYPE_VOID,  4, None),
    0x18: ("JR r8",           2, TYPE_R8,   12, None),
    0x19: ("ADD HL, DE",      1, TYPE_VOID,  8, (None, 0, "H", "C")),
    0x1a: ("LD A, (DE)",      1, TYPE_VOID, 18, None),
    0x1b: ("DEC DE",          1, TYPE_VOID,  8, None),
    0x1c: ("INC E",           1, TYPE_VOID,  4, ("Z", 0, "H")),
    0x1d: ("DEC E",           1, TYPE_VOID,  4, ("Z", 1, "H")),
    0x1e: ("LD E, d8",        2, TYPE_D8,    8, None),
    0x1f: ("RRA",             1, TYPE_VOID,  4, (0, 0, 0, "C")),
    0x20: ("JR NZ, r8",       2, TYPE_R8,  (12, 8), None),
    0x21: ("LD HL, d16",      3, TYPE_D16,  12, None),
    0x22: ("LD (HL+), A",     1, TYPE_VOID,  8, None),
    0x23: ("INC HL",          1, TYPE_VOID,  8, None),
    0x24: ("INC H",           1, TYPE_VOID,  4, ("Z", 0, "H")),
    0x25: ("DEC H",           1, TYPE_VOID,  4, ("Z", 1, "H")),
    0x26: ("LD H, d8",        2, TYPE_D8,    8, None),
    0x27: ("DAA",             1, TYPE_VOID,  4, ("Z", None, 0, "C")),
    0x28: ("JR Z, r8",        2, TYPE_VOID, (12, 8), None),
    0x29: ("ADD HL, HL",      1, TYPE_VOID,  8, (None, 0, "H", "C")),
    0x2a: ("LD A, (HL+)",     1, TYPE_VOID,  8, None),
    0x2b: ("DEC HL",          1, TYPE_VOID,  8, None),
    0x2c: ("INC L",           1, TYPE_VOID,  4, ("Z", 0, "H")),
    0x2d: ("DEC L",           1, TYPE_VOID,  4, ("Z", 1, "H")),
    0x2e: ("LD L, d8",        2, TYPE_D8,    8, None),
    0x2f: ("CPL",             1, TYPE_VOID,  4, (None, 1, 1, None)),
    0x30: ("JR NC, r8",       2, TYPE_R8,  (12, 8), None),
    0x31: ("LD SP, d16",      3, TYPE_D16,  12, None),
    0x32: ("LD (HL-), A",     1, TYPE_VOID,  8, None),
    0x33: ("INC SP",          1, TYPE_VOID,  8, None),
    0x34: ("INC (HL)",        1, TYPE_VOID, 12, ("Z", 0, "H")),
    0x35: ("DEC (HL)",        1, TYPE_VOID, 12, ("Z", 1, "H")),
    0x36: ("LD (HL), d8",     2, TYPE_D8,   12, None),
    0x37: ("SCF",             1, TYPE_VOID,  4, (None, 0, 0, 1)),
    0x38: ("JR C, r8",        2, TYPE_R8,  (12, 8), None),
    0x3c: ("INC A",           1, TYPE_VOID,  4, ("Z", 0, "H")),
    0x3d: ("DEC A",           1, TYPE_VOID,  4, ("Z", 1, "H")),
    0x3e: ("LD A, d8",        2, TYPE_D8,    8, None),
    0x3f: ("CCF",             1, TYPE_VOID,  4, (None, 0, 0, "C")),
    0x40: ("LD B, B",         1, TYPE_VOID,  4, None),
    0x41: ("LD B, C",         1, TYPE_VOID,  4, None),
    0x42: ("LD B, D",         1, TYPE_VOID,  4, None),
    0x43: ("LD B, E",         1, TYPE_VOID,  4, None),
    0x44: ("LD B, H",         1, TYPE_VOID,  4, None),
    0x45: ("LD B, L",         1, TYPE_VOID,  4, None),
    0x46: ("LD B, (HL)",      1, TYPE_VOID,  8, None),
    0x47: ("LD B, A",         1, TYPE_VOID,  4, None),
    0x48: ("LD C, B",         1, TYPE_VOID,  4, None),
    0x49: ("LD C, C",         1, TYPE_VOID,  4, None),
    0x4a: ("LD C, D",         1, TYPE_VOID,  4, None),
    0x4b: ("LD C, E",         1, TYPE_VOID,  4, None),
    0x4c: ("LD C, H",         1, TYPE_VOID,  4, None),
    0x4d: ("LD C, L",         1, TYPE_VOID,  4, None),
    0x4e: ("LD C, (HL)",      1, TYPE_VOID,  8, None),
    0x4f: ("LD C, A",         1, TYPE_VOID,  4, None),
    0x50: ("LD D, B",         1, TYPE_VOID,  4, None),
    0x51: ("LD D, C",         1, TYPE_VOID,  4, None),
    0x52: ("LD D, D",         1, TYPE_VOID,  4, None),
    0x53: ("LD D, E",         1, TYPE_VOID,  4, None),
    0x54: ("LD D, H",         1, TYPE_VOID,  4, None),
    0x55: ("LD D, L",         1, TYPE_VOID,  4, None),
    0x56: ("LD D, (HL)",      1, TYPE_VOID,  8, None),
    0x57: ("LD D, A",         1, TYPE_VOID,  4, None),
    0x58: ("LD E, B",         1, TYPE_VOID,  4, None),
    0x59: ("LD E, C",         1, TYPE_VOID,  4, None),
    0x5a: ("LD E, D",         1, TYPE_VOID,  4, None),
    0x5b: ("LD E, E",         1, TYPE_VOID,  4, None),
    0x5c: ("LD E, H",         1, TYPE_VOID,  4, None),
    0x5d: ("LD E, L",         1, TYPE_VOID,  4, None),
    0x5e: ("LD E, (HL)",      1, TYPE_VOID,  8, None),
    0x5f: ("LD E, A",         1, TYPE_VOID,  4, None),
    0x60: ("LD H, B",         1, TYPE_VOID,  4, None),
    0x61: ("LD H, C",         1, TYPE_VOID,  4, None),
    0x62: ("LD H, D",         1, TYPE_VOID,  4, None),
    0x63: ("LD H, E",         1, TYPE_VOID,  4, None),
    0x64: ("LD H, H",         1, TYPE_VOID,  4, None),
    0x65: ("LD H, L",         1, TYPE_VOID,  4, None),
    0x66: ("LD H, (HL)",      1, TYPE_VOID,  8, None),
    0x67: ("LD H, A",         1, TYPE_VOID,  4, None),
    0x68: ("LD L, B",         1, TYPE_VOID,  4, None),
    0x69: ("LD L, C",         1, TYPE_VOID,  4, None),
    0x6a: ("LD L, D",         1, TYPE_VOID,  4, None),
    0x6b: ("LD L, E",         1, TYPE_VOID,  4, None),
    0x6c: ("LD L, H",         1, TYPE_VOID,  4, None),
    0x6d: ("LD L, L",         1, TYPE_VOID,  4, None),
    0x6e: ("LD L, (HL)",      1, TYPE_VOID,  8, None),
    0x6f: ("LD L, A",         1, TYPE_VOID,  4, None),
    0x70: ("LD (HL), B",      1, TYPE_VOID,  8, None),
    0x71: ("LD (HL), C",      1, TYPE_VOID,  8, None),
    0x72: ("LD (HL), D",      1, TYPE_VOID,  8, None),
    0x73: ("LD (HL), E",      1, TYPE_VOID,  8, None),
    0x74: ("LD (HL), H",      1, TYPE_VOID,  8, None),
    0x75: ("LD (HL), L",      1, TYPE_VOID,  8, None),
    0x76: ("HALT",            1, TYPE_VOID,  4, None),
    0x77: ("LD (HL), A",      1, TYPE_VOID,  8, None),
    0x78: ("LD A, B",         1, TYPE_VOID,  4, None),
    0x79: ("LD A, C",         1, TYPE_VOID,  4, None),
    0x7a: ("LD A, B",         1, TYPE_VOID,  4, None),
    0x7b: ("LD A, E",         1, TYPE_VOID,  4, None),
    0x7c: ("LD A, H",         1, TYPE_VOID,  4, None),
    0x7d: ("LD A, L",         1, TYPE_VOID,  4, None),
    0x7e: ("LD A, (HL)",      1, TYPE_VOID,  8, None),
    0x7f: ("LD A, A",         1, TYPE_VOID,  4, None),
    0x80: ("ADD A, B",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x81: ("ADD A, C",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x82: ("ADD A, D",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x83: ("ADD A, E",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x84: ("ADD A, H",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x85: ("ADD A, L",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x86: ("ADD A, (HL)",     1, TYPE_VOID,  8, ("Z", 0, "H", "C")),
    0x87: ("ADC A, A",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x88: ("ADC A, B",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x89: ("ADC A, C",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x8a: ("ADC A, D",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x8b: ("ADC A, E",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x8c: ("ADC A, H",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x8d: ("ADC A, L",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x8e: ("ADC A, (HL)",     1, TYPE_VOID,  8, ("Z", 0, "H", "C")),
    0x8f: ("ADC A, A",        1, TYPE_VOID,  4, ("Z", 0, "H", "C")),
    0x90: ("SUB B",           1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0x91: ("SUB C",           1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0x92: ("SUB D",           1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0x93: ("SUB E",           1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0x94: ("SUB H",           1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0x95: ("SUB L",           1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0x96: ("SUB (HL)",        1, TYPE_VOID,  8, ("Z", 1, "H", "C")),
    0x97: ("SUB A",           1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0x98: ("SBC A, B",        1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0x99: ("SBC A, C",        1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0x9a: ("SBC A, D",        1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0x9b: ("SBC A, E",        1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0x9c: ("SBC A, H",        1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0x9d: ("SBC A, L",        1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0x9e: ("SBC A, (HL)",     1, TYPE_VOID,  8, ("Z", 1, "H", "C")),
    0x9f: ("SBC A, A",        1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0xa0: ("AND B",           1, TYPE_VOID,  4, ("Z", 0, 1, 0)),
    0xa1: ("AND C",           1, TYPE_VOID,  4, ("Z", 0, 1, 0)),
    0xa2: ("AND D",           1, TYPE_VOID,  4, ("Z", 0, 1, 0)),
    0xa3: ("AND E",           1, TYPE_VOID,  4, ("Z", 0, 1, 0)),
    0xa4: ("AND H",           1, TYPE_VOID,  4, ("Z", 0, 1, 0)),
    0xa5: ("AND L",           1, TYPE_VOID,  4, ("Z", 0, 1, 0)),
    0xa6: ("AND (HL)",        1, TYPE_VOID,  8, ("Z", 0, 1, 0)),
    0xa7: ("AND A",           1, TYPE_VOID,  4, ("Z", 0, 1, 0)),
    0xa8: ("XOR B",           1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xa9: ("XOR C",           1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xaa: ("XOR D",           1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xab: ("XOR E",           1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xac: ("XOR H",           1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xad: ("XOR L",           1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xae: ("XOR (HL)",        1, TYPE_VOID,  8, ("Z", 0, 0, 0)),
    0xaf: ("XOR A",           1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xb0: ("OR B",            1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xb1: ("OR C",            1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xb2: ("OR D",            1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xb3: ("OR E",            1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xb4: ("OR H",            1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xb5: ("OR L",            1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xb6: ("OR (HL)",         1, TYPE_VOID,  8, ("Z", 0, 0, 0)),
    0xb7: ("OR A",            1, TYPE_VOID,  4, ("Z", 0, 0, 0)),
    0xb8: ("CP B",            1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0xb9: ("CP C",            1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0xba: ("CP D",            1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0xbb: ("CP E",            1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0xbc: ("CP H",            1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0xbd: ("CP L",            1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0xbe: ("CP (HL)",         1, TYPE_VOID,  8, ("Z", 1, "H", "C")),
    0xbf: ("CP A",            1, TYPE_VOID,  4, ("Z", 1, "H", "C")),
    0xc0: ("RET NZ",          1, TYPE_VOID, (20, 8), None),
    0xc1: ("POP BC",          1, TYPE_VOID,  12, None),
    0xc2: ("JP NZ, a16",      3, TYPE_A16,  (16, 12), None),
    0xc3: ("JP a16",          3, TYPE_A16,   16, None),
    0xc4: ("CALL NZ, a16",    3, TYPE_A16,  (24, 12), None),
    0xc5: ("PUSH BC",         1, TYPE_VOID,  16, None),
    0xc6: ("ADD A, d8",       2, TYPE_VOID,   8, ("Z", 0, "H", "C")),
    0xc7: ("RST 00H",         1, TYPE_VOID,  16, None),
    0xc8: ("RET Z",           1, TYPE_VOID, (20, 8), None),
    0xc9: ("RET",             1, TYPE_VOID,  16, None),
    0xca: ("JP Z, a16",       3, TYPE_A16,  (16, 12), None),
    0xcb: ("PREFIX CB",       1, TYPE_VOID,   4, None),
    0xcc: ("CALL Z, a16",     3, TYPE_A16,  (24, 12), None),
    0xcd: ("CALL a16",        3, TYPE_A16,   24, None),
    0xce: ("ADC A, d8",       2, TYPE_D8,     8, ("Z", 0, "H", "C")),
    0xcf: ("RST 08H",         1, TYPE_VOID,  16, None),
    0xd0: ("RET NC",          1, TYPE_VOID, (20, 8), None),
    0xd1: ("POP DE",          1, TYPE_VOID,  12, None),
    0xd2: ("JP NC, a16",      1, TYPE_A16,  (16, 12), None),
    0xd3: ("-",               1, TYPE_VOID,   0, None),
    0xd4: ("CALL NC, a16",    3, TYPE_A16,  (24, 12), None),
    0xd5: ("PUSH DE",         1, TYPE_VOID,  16, None),
    0xd6: ("SUB d8",          2, TYPE_D8,     8, ("Z", 1, "H", "C")),
    0xd7: ("RST 10H",         1, TYPE_VOID,  16, None),
    0xd8: ("RET C",           1, TYPE_VOID, (20, 8), None),
    0xd9: ("RETI",            1, TYPE_VOID,  16, None),
    0xda: ("JP C, a16",       3, TYPE_A16,  (20, 12), None),
    0xdb: ("-",               1, TYPE_VOID,   0, None),
    0xdc: ("CALL C, a16",     3, TYPE_A16,  (24, 12), None),
    0xdd: ("-",               1, TYPE_VOID,   0, None),
    0xde: ("SBC A, d8",       2, TYPE_D8,     8, ("Z", 1, "H", "C")),
    0xdf: ("RST 18H",         1, TYPE_VOID,  16, None),
    0xe0: ("LD (a8), A",      2, TYPE_A8,    12, None), # NOTE: Some say LDH
    0xe1: ("POP HL",          1, TYPE_VOID,  12, None),
    0xe2: ("LD ($ff00+C), A", 1, TYPE_VOID,   8, None),
    0xe3: ("-",               1, TYPE_VOID,   0, None),
    0xe4: ("-",               1, TYPE_VOID,   0, None),
    0xe5: ("PUSH HL",         1, TYPE_VOID,  16, None),
    0xe6: ("AND d8",          2, TYPE_D8,     8, ("Z", 0, 1, 0)),
    0xe7: ("RST 20H",         1, TYPE_VOID,  16, None),
    0xe8: ("ADD SP, r8",      2, TYPE_R8,    16, (0, 0, "H", "C")),
    0xe9: ("JP (HL)",         1, TYPE_VOID,   4, None),
    0xea: ("LD (a16), A",     3, TYPE_A16,   16, None),
    0xeb: ("-",               1, TYPE_VOID,   0, None),
    0xec: ("-",               1, TYPE_VOID,   0, None),
    0xed: ("-",               1, TYPE_VOID,   0, None),
    0xee: ("XOR d8",          2, TYPE_R8,     8, ("Z", 0, 0, 0)),
    0xef: ("RST 28H",         1, TYPE_VOID,  16, None),
    0xf0: ("LDH A, (a8)",     2, TYPE_A8,    12, None),
    0xf1: ("POP AF",          1, TYPE_VOID,  12, ("Z", "N", "H", "C")),
    0xf2: ("LD A, (C)",       2, TYPE_VOID,   8, None),
    0xf3: ("DI",              1, TYPE_VOID,   4, None),
    0xf4: ("-",               1, TYPE_VOID,   0, None),
    0xf5: ("PUSH AF",         1, TYPE_VOID,  16, None),
    0xf6: ("OR d8",           2, TYPE_D8,     8, None),
    0xf7: ("RST 30H",         1, TYPE_VOID,  16, None),
    0xf8: ("LD HL, SP+r8",    2, TYPE_R8,    12, (0, 0, "H", "C")),
    0xf9: ("LD SP, HL",       1, TYPE_VOID,   8, None), # NOTE: Nintendo manual says 2 cycles?
    0xfa: ("LD A, (a16)",     3, TYPE_A16,   16, None),
    0xfb: ("EI",              1, TYPE_VOID,   4, None),
    0xfc: ("-",               1, TYPE_VOID,   0, None),
    0xfd: ("-",               1, TYPE_VOID,   0, None),
    0xfe: ("CP d8",           2, TYPE_D8,     8, ("Z", 1, "H", "C")),
    0xff: ("RST 38H",         1, TYPE_VOID,  16, None),
}
