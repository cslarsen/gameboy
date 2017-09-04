import array
import random
import sys

def make_array(data=None):
    """Creates an array consisting of unsigned 8-bit bytes."""
    if data is None:
        return array.array("B")
    else:
        return array.array("B", data)

def load_binary(filename):
    """Reads a binary file into an unsigned 8-bit array."""
    with open(filename, "rb") as f:
        return make_array(f.read())

def u8_to_signed(value):
    """Converts an unsigned 8-bit byte to a signed byte."""
    assert(0 <= value <= 0xff)

    if value > 0x7f:
        return -(0x100 - value)
    else:
        return value

def u16_to_u8(value):
    """Little-endian splitting of 16-bit word to 8-bit byte.

    Returns (high u8, low u8).
    """
    assert(0 <= value <= 0xffff)
    lo = value & 0xff
    hi = (value & 0xff00) >> 8
    return (hi, lo)

def u8_to_u16(hi, lo):
    assert(0 <= lo <= 0xff)
    assert(0 <= hi <= 0xff)
    return hi << 8 | lo

def format_bin(value, bits=8):
    s = bin(value)[2:]
    return "0"*(bits-len(s)) + s

def format_hex(value, prefix="$"):
    """Formats a hex value that is suitable for Gameboy disassembly."""
    sign = "" if value>=0 else "-"
    if abs(value) <= 0xff:
        return "%s%s%0.2x" % (sign, prefix, abs(value))
    else:
        return "%s%s%0.4x" % (sign, prefix, abs(value))

def make_randomized_array(length):
    """Creates an array filled with random 8-bit unsigned bytes."""
    r = make_array()

    for i in range(length):
        r.append(random.randint(0x00, 0xff))

    return r

def log(msg, nl=True):
    sys.stdout.write("%s%s" % (msg, "\n" if nl else ""))
    sys.stdout.flush()

def dot(*args):
    sys.stdout.write(" ".join(map(str, args)))
    sys.stdout.flush()

def wait_enter(prefix):
    if sys.version_info.major < 3:
        return raw_input(prefix)
    else:
        return input(prefix)

POST_BOOT_STATE = {
    "registers": {
        "A": 0x01, # GB/SGB
        "B": 0x00,
        "C": 0x13,
        "D": 0x00,
        "E": 0xd8,
        "F": 0xb0,
        "H": 0x01,
        "L": 0xfd,
        "SP": 0xfffe,
        "PC": 0x0100,
    },
    "memory": {
        0xff05: 0x00, # TIMA
        0xff06: 0x00, # TMA
        0xff07: 0x00, # TAC
        0xff10: 0x80, # NR10
        0xff11: 0xbf, # NR11
        0xff12: 0xf3, # NR12
        0xff14: 0xbf, # NR14
        0xff16: 0x3f, # NR21
        0xff17: 0x00, # NR22
        0xff19: 0xbf, # NR24
        0xff1a: 0x7f, # NR30
        0xff1b: 0xff, # NR31
        0xff1c: 0x9f, # NR32
        0xff1e: 0xbf, # NR33
        0xff20: 0xff, # NR41
        0xff21: 0x00, # NR42
        0xff22: 0x00, # NR43
        0xff23: 0xbf, # NR30
        0xff24: 0x77, # NR50
        0xff25: 0xf3, # NR51
        0xff26: 0xf1, # NR52: 0xf1=GB, 0xf0=SGB
        0xff40: 0x91, # LCDC
        0xff42: 0x00, # SCY
        0xff43: 0x00, # SCX
        0xff45: 0x00, # LYC
        0xff47: 0xfc, # BGP
        0xff48: 0xff, # OBP0
        0xff49: 0xff, # OBP1
        0xff4a: 0x00, # WY
        0xff4b: 0x00, # WX
        0xffff: 0x00, # IE
    }
}

def set_boot(cpu):
    """Initialises GameBoy to the state right after completing the boot
    code."""
    register = POST_BOOT_STATE["registers"]

    cpu.A = register["A"]
    cpu.B = register["B"]
    cpu.C = register["C"]
    cpu.D = register["D"]
    cpu.E = register["E"]
    cpu.F = register["F"]
    cpu.H = register["H"]
    cpu.L = register["L"]
    cpu.SP = register["SP"]
    cpu.PC = register["PC"]

    memory = POST_BOOT_STATE["memory"]
    for address, value in sorted(memory.items()):
        cpu.memory[address] = value

    # Because writes go through the memory controller, check that they are
    # correct.
    check_boot(cpu)

def check_boot(cpu):
    """Checks that the GameBoy is in the correct state after completing the
    boot code."""
    # Anything wrong here means that the implementation executes the boot code
    # incorrectly.
    register = POST_BOOT_STATE["registers"]
    ok = True

    def assert_register(name, actual, expected):
        if actual != expected:
            ok = False
            log("Register %s=$%0.2x but should be $%0.2x" % (
                name, actual, expected))

    assert_register("A", cpu.A, register["A"])
    assert_register("B", cpu.B, register["B"])
    assert_register("C", cpu.C, register["C"])
    assert_register("D", cpu.D, register["D"])
    assert_register("E", cpu.E, register["E"])
    assert_register("F", cpu.F, register["F"])
    assert_register("H", cpu.H, register["H"])
    assert_register("L", cpu.L, register["L"])
    assert_register("SP", cpu.SP, register["SP"])
    assert_register("PC", cpu.PC, register["PC"])

    memory = POST_BOOT_STATE["memory"]
    for address, expected in sorted(memory.items()):
        actual = cpu.memory[address]
        if actual != expected:
            ok = False
            log("Memory location $%0.4x=$%0.2x but should be $%0.2x" % (
                address, actual, expected))

    return ok
