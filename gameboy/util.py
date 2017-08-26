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

def format_hex(value):
    """Formats a hex value that is suitable for Gameboy disassembly."""
    sign = "" if value>=0 else "-"
    if abs(value) <= 0xff:
        return "%s$%0.2x" % (sign, abs(value))
    else:
        return "%s$%0.4x" % (sign, abs(value))

def make_randomized_array(length):
    """Creates an array filled with random 8-bit unsigned bytes."""
    r = make_array()

    for i in range(length):
        r.append(random.randint(0x00, 0xff))

    return r

def log(msg):
    sys.stdout.write("%s\n" % msg)
    sys.stdout.flush()

def wait_enter(prefix):
    if sys.version_info.major < 3:
        return raw_input(prefix)
    else:
        return input(prefix)
