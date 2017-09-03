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
        return "<Cartridge: title=%r color=%r sgb=%r type=%r bytes=$%x ROM banks=%d, RAM banks=%s>" % (
                self.title, self.color, self.super_gameboy, self.type,
                len(self), self.rom_banks, self.ram_banks)

    @property
    def title(self):
        """Title of game in uppercase ASCII."""
        s = self.rom_bank[0][0x0134:0x0142]
        s = str(s.tostring().decode("ascii"))
        if "\0" in s:
            s = s[:s.index("\0")]
        return s

    @property
    def color(self):
        return self.rom_bank[0][0x143] == 0x80

    @property
    def rom_banks(self):
        size = self.rom_bank[0][0x148]
        return {
            0x0: 2,
            0x1: 4,
            0x2: 8,
            0x3: 16,
            0x4: 32,
            0x5: 64,
            0x6: 128,
            0x52: 72,
            0x53: 80,
            0x54: 96,
        }.get(size)

    @property
    def ram_banks(self):
        return {
            0: None,
            1: 1,
            2: 1,
            3: 4,
            4: 16,
        }.get(self.rom_bank[0][0x149])

    @property
    def destination_code(self):
        return {
            0: "Japanese",
            1: "Non-Japanese",
        }.get(self.rom_bank[0][0x14a])

    @property
    def super_gameboy(self):
        """Whether this is a classic GameBoy or Super GameBoy cartridge."""
        t = self.rom_bank[0][0x146]

        if t == 0x00:
            return False # Gameboy
        if t == 0x03:
            return True # Super Gameboy functions

        raise RuntimeError("Invalid cartridge type %0.2x" % t)

    @property
    def type(self):
        """Cartridge type."""
        return {
            0x00: "ROM only",
            0x01: "ROM + MBC1",
            0x02: "ROM + MBC1 + RAM",
            0x03: "ROM + MBC1 + RAM + BATTERY",
            0x05: "ROM + MBC2",
            0x06: "ROM + MBC2 + BATTERY",
            0x08: "ROM + RAM",
            0x09: "ROM + RAM + BATTERY",
            0x0b: "ROM + MMM01",
            0x0c: "ROM + MMM01 + SRAM",
            0x0d: "ROM + MMM01 + SRAM + BATTERY",
            0x0f: "ROM + MBC3 + TIMER + BATTERY",
            0x10: "ROM + MBC3 + TIMER + RAM + BATTERY",
            0x11: "ROM + MBC3",
            0x12: "ROM + MBC3 + RAM",
            0x13: "ROM + MBC3 + RAM + BATTERY",
            0x19: "ROM + MBC5",
            0x1a: "ROM + MBC5 + RAM",
            0x1b: "ROM + MBC5 + RAM + BATTERY",
            0x1c: "ROM + MBC5 + RUMBLE",
            0x1d: "ROM + MBC5 + RUMBLE + SRAM",
            0x1e: "ROM + MBC5 + RUMBLE + SRAM + BATTERY",
            0x1f: "Pocket Camera",
            0xfd: "Bandai TAMA5",
            0xfe: "Hudson HuC-3",
            0xff: "Hudson HuC-1",
        }.get(self.rom_bank[0][0x147], "Unknown")
