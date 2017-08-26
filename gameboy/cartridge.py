from memory import Memory

class Cartridge(object):
    def __init__(self, rom=None):
        if rom is None:
            self.rom_bank = [Memory(0x4000, readonly=True)]*16
        else:
            # Divide rom up into 16kB banks
            self.rom_bank = []
            for n in range(16):
                start = 0x4000*n
                end = start + 0x4000 - 1
                try:
                    self.rom_bank.append(Memory(rom[start:end], readonly=True))
                except IndexError:
                    break

    @property
    def title(self):
        """Title of game in upper case ascii."""
        s = self.rom_bank[0][0x0134:0x0142].tostring().decode("ascii")
        s = s[:s.index("\0")]
        return s

    @property
    def type(self):
        """Whether this is a classic GameBoy or Super GameBoy cartridge."""
        t = self.rom_bank[0][0x146]

        if t == 0x00:
            return "GameBoy"
        if t == 0x03:
            return "Super GameBoy"

        raise RuntimeError("Invalid cartridge type %0.2x" % t)
