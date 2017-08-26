from memory import Memory

class Cartridge(object):
    def __init__(self, rom=None):
        if rom is None:
            self.rom_bank = [Memory(0x4000, readonly=True,
                                    name="Cartridge ROM bank")]*16
        else:
            # Divide rom up into 16kB banks
            self.rom_bank = []

            length = len(rom)
            start = 0
            while start < length:
                end = start + 0x4000
                if end < length:
                    self.rom_bank.append(Memory(rom[start:end], readonly=True,
                        name="Cartridge ROM bank #%d" % len(self.rom_bank)))
                    start += 0x4000
                else:
                    self.rom_bank.append(Memory(rom[start:], readonly=True,
                        name="Cartridge ROM bank #%d" % len(self.rom_bank)))
                    break

    def __len__(self):
        return sum(map(len, self.rom_bank))

    def __repr__(self):
        return "<Cartridge: title=%r type=%r bytes=0x%x>" % (
                self.title, self.type, len(self))

    @property
    def title(self):
        """Title of game in uppercase ASCII."""
        s = self.rom_bank[0][0x0134:0x0142]
        s = str(s.tostring().decode("ascii"))
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
