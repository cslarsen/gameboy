from array import array

class Cartridge(object):
    def __init__(self, rom=None):
        self.rom = array("B", [0]*32768) if rom is None else rom
        assert(len(self.rom) >= 32768)

    @property
    def title(self):
        """Title of game in upper case ascii."""
        s = self.rom[0x0134:0x0142].tostring().decode("ascii")
        s = s[:s.index("\0")]
        return s

    @property
    def type(self):
        """Whether this is a classic GameBoy or Super GameBoy cartridge."""
        t = self.rom[0x146]

        if t == 0x00:
            return "GameBoy"
        if t == 0x03:
            return "Super GameBoy"

        raise RuntimeError("Invalid cartridge type %0.2x" % t)
