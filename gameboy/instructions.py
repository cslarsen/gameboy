def swap8(n):
    """Swaps high and low nibbles in 8-bit byte."""
    return (n & 0xf) << 4 | n >> 4
