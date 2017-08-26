"""
Contains opcodes for the 8-bit Sharp LR35902 CPU running at 4.19 MHz. This CPU
is similar to the Zilog Z80 and Intel 8080 CPUs.

The opcode maps machine code to
    - (name, arguments ...)
    - bytelength
    - cycle duration (two values: cycles if taken/not taken),
    - affected flags (always in ZHNC order; 0 means reset after run)

The mnemonics follow http://pastraiser.com/cpu/gameboy/gameboy_opcodes.html

NOTE: Instruction 0xe2 is said to take two bytes (one 8-bit argument), but from
elsewhere it seems like it only takes one. For example, see
https://stackoverflow.com/a/41422692/21028
"""

opcodes = {
    0x00: ("NOP",               1,  4, None),
    0x01: ("LD BC, d16",        3, 12, None),
    0x02: ("LD (BC), A",        1,  8, None),
    0x03: ("INC BC",            1,  8, None),
    0x04: ("INC B",             1,  4, ("Z", "0", "H")),
    0x05: ("DEC B",             1,  4, ("Z", "1", "H")),
    0x06: ("LD B, d8",          2,  8, None),
    0x08: ("LD (a16), SP",      3, 20, None), # NOTE: Unverified
    0x0b: ("DEC BC",            1,  8, None), # NOTE: Unverified
    0x0c: ("INC C",             1,  4, ("Z", "0", "H")),
    0x0d: ("DEC C",             1,  4, ("Z", "1", "H")),
    0x0e: ("LD C, d8",          2,  8, None),
    0x10: ("STOP",              2,  4, None),
    0x11: ("LD DE, d16",        3, 12, None),
    0x13: ("INC DE",            1,  8, None),
    0x15: ("DEC D",             1,  4, ("Z", "1", "H")),
    0x16: ("LD D, d8",          2,  8, None),
    0x17: ("RLA",               1,  4, None),
    0x18: ("JR r8",             2, 12, None),
    0x1a: ("LD A, (DE)",        1, 18, None),
    0x1d: ("DEC E",             1,  4, ("Z", "1", "H")),
    0x1e: ("LD E, d8",          2,  8, None),
    0x20: ("JR NZ, r8",         2, (12, 8), None),
    0x21: ("LD HL, d16",        3, 12, None),
    0x22: ("LD (HL+), A",       1,  8, None),
    0x23: ("INC HL",            1,  8, None),
    0x24: ("INC H",             1,  4, ("Z", "0", "H")),
    0x28: ("JR Z, r8",          2, (12, 8), None),
    0x2e: ("LD L, d8",          2,  8, None),
    0x31: ("LD SP, d16",        3, 12, None),
    0x32: ("LD (HL-), A",       1,  8, None),
    0x33: ("INC SP",            1,  8, None), # NOTE: Unverified
    0x3c: ("INC A",             1,  4, ("Z", "0", "H")), # NOTE: Unverified
    0x3d: ("DEC A",             1,  4, ("Z", "1", "H")),
    0x3e: ("LD A, d8",          2,  8, None),
    0x42: ("LD B, D",           1,  4, None), # NOTE: Unverified
    0x4f: ("LD C, A",           1,  4, None),
    0x57: ("LD D, A",           1,  4, None),
    0x63: ("LD H, E",           1,  4, None), # NOTE: Unverified
    0x66: ("LD H, (HL)",        1,  8, None), # NOTE: Unverified
    0x67: ("LD H, A",           1,  4, None),
    0x6e: ("LD L, (HL)",        1,  8, None), # NOTE: Unverified
    0x73: ("LD (HL), E",        1,  8, None), # NOTE: Unverified
    0x76: ("HALT",              1,  4, None),
    0x77: ("LD (HL), A",        1,  8, None),
    0x78: ("LD A, B",           1,  4, None), # NOTE: Unverified
    0x7b: ("LD A, E",           1,  4, None),
    0x7c: ("LD A, H",           1,  4, None),
    0x7d: ("LD A, L",           1,  4, None), # NOTE: Unverified
    0x83: ("ADD A, E",          1,  4, ("Z", "0", "H", "C")), # NOTE: Unverified
    0x86: ("ADD A, (HL)",       1,  8, ("Z", "0", "H", "C")), # NOTE: Unverified, some say just "ADD (HL)"
    0x88: ("ADC A, B",          1,  4, ("Z", "0", "H", "C")), # NOTE: Unverified
    0x89: ("ADC A, C",          1,  4, ("Z", "0", "H", "C")), # NOTE: Unverified
    0x90: ("SUB B",             1,  4, ("Z", "1", "H", "C")),
    0x99: ("SBC A, C",          1,  4, ("Z", "1", "H", "C")), # NOTE: Unverified
    0x9f: ("SBC A, A",          1,  4, ("Z", "1", "H", "C")),
    0xa5: ("AND L",             1,  4, ("Z", "0", "1", "0")), # NOTE: Unverified
    0xaf: ("XOR A",             1,  4, ("Z", "0", "0", "0")),
    0xb9: ("CP C",              1,  4, ("Z", "1", "H", "C")), # NOTE: Unverified
    0xbb: ("CP E",              1,  4, ("Z", "1", "H", "C")), # NOTE: Unverified
    0xbe: ("CP (HL)",           1,  8, ("Z", "1", "H", "C")), # NOTE: Unverified
    0xc1: ("POP BC",            1, 12, None),
    0xc5: ("PUSH BC",           1, 16, None),
    0xc9: ("RET",               1, 16, None),
    0xcb: ("PREFIX CB",         1,  4, None),
    0xcc: ("CALL Z, a16",       3, (24, 12), None), # NOTE: Unverified
    0xcd: ("CALL a16",          3, 24, None),
    0xce: ("ADD A, d8",         2,  8, ("Z", "0", "H", "C")),
    0xd9: ("RETI",              1, 16, None), # NOTE: Unverified
    0xdd: ("-",                 1,  0, None), # NOTE: Invalid instruction
    0xe0: ("LDH (a8), A",       2, 12, None), # NOTE: Others say LD, not LDH
    0xe2: ("LD ($ff00+C), A",   1,  8, None), # NOTE: Above link says 2 bytes!
    0xea: ("LD (a16), A",       3, 16, None),
    0xf0: ("LDH A, (a8)",       2, 12, None),
    0xf3: ("DI",                1,  4, None),
    0xf7: ("RST 30H",           1, 16, None),
    0xf9: ("LD SP, HL",         1,  8, None),
    0xfa: ("LD A, (a16)",       3, 16, None),
    0xfb: ("EI",                1,  4, None),
    0xfe: ("CP d8",             2,  8, ("Z", "1", "H", "C")),
    0xff: ("RST 38H",           1, 16, None),
}

# Extended opcodes. Use this table after the opcode 0xcb has been encountered
# from the preceding table. BYte lengths here are EXCLUSIVE the preceding
# prefix opcode.
extended_opcodes = {
    0x11: ("RL C",              1, 8, ("Z", "0", "0", "C")),
    0x7c: ("BIT 7, H",          1, 8, ("Z", "0", "1")),
}

# Opcodes whose argument should be added with 0xff00
add_0xff00_opcodes = (
    0xe0,
    0xe2,
    0xf0,
)
