def swap8(n):
    """Swaps high and low nibbles in 8-bit byte."""
    return (n & 0xf) << 4 | n >> 4

def inc16(n):
    return (n + 1) % 0xffff
