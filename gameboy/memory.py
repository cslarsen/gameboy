from util import make_randomized_array

class MemoryController(object):
    def __init__(self, boot_rom, display, cartridge):
        self.internal_ram = make_randomized_array(8192)
        self.display = display
        self.cartridge = cartridge

        self.boot_rom = boot_rom

        # Current bank at 0x0000 and out
        self.bank = boot_rom

        # 8kB switchable RAM banks
        self.banks = [
            make_randomized_array(8192),
        ]

    def __getitem__(self, address):
        """Reads one memory byte.

        Here we are accessing memory based on CPU address
        """
        assert(0 <= address <= 0xffff)

        # e000-fe00 mirrored in c000-de00

        if address < 0x4000:
            rom = self.bank
            return rom[address]
        elif address < 0x8000:
            raise NotImplementedError()
        elif address < 0xa000:
            return self.display.ram[address - 0x8000]
        elif address < 0xc000:
            ram_bank = self.banks[self.bank]
            return ram_bank[address - 0xa000]
        elif address < 0xe000:
            # 8 kB
            return self.internal_ram[address - 0xc000]
        elif address  < 0xfe00:
            # echo of 8 kB internal RAM
            return self.internal_ram[address - 0xc000]
        else:
            # sprite attribute memory...
            raise NotImplementedError()

    def __setitem__(self, address, value):
        """Reads one memory byte.

        Here we are accessing memory based on CPU address
        """
        assert(0 <= address <= 0xffff)

        if address < 0x4000:
            rom = self.bank
            rom[address] = value
        elif address < 0x8000:
            raise NotImplementedError()
        elif address < 0xa000:
            self.display.ram[address - 0x8000] = value
        elif address < 0xc000:
            ram_bank = self.banks[self.bank]
            ram_bank[address - 0xa000] = value
        elif address < 0xe000:
            # 8 kB
            self.internal_ram[address - 0xc000] = value
        elif address  < 0xfe00:
            self.internal_ram[address - 0xc000] = value
        else:
            # sprite attribute memory...
            raise NotImplementedError()

    def get16(self, address):
        # Little-endian
        return u8_to_u16(self[address], self[address+1])

    def set16(self, address, value):
        # Little-endian
        self[address:address+1] = u16_to_u8(value)
