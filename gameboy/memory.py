from util import make_randomized_array

class MemoryController(object):
    def __init__(self, boot_rom, display, cartridge):
        self.ram = make_randomized_array(8000)
        self.display = display
        self.cartridge = cartridge
        self.boot_rom = boot_rom

        # On startup, copy code from boot rom into ordinary ram
        self.ram[:len(boot_rom)] = boot_rom
        self.booting = True

    def __getitem__(self, address):
        """Reads one memory byte."""
        assert(0 <= address <= 0xffff)

        if address < 0x8000:
            if self.booting:
                # TODO: I think the bank switching may come into play here.
                # Investigate.
                return self.ram[address]
            else:
                return self.cartridge.rom[address]
        elif address < 0xa000:
            return self.display.ram[address-0x8000]
        elif address < 0xc000:
            return self.ram[address-0xa000]

    def __setitem__(self, address, value):
        """Writes one or several bytes in memory."""
        assert(0 <= address <= 0xffff)
        assert(value <= 0xff)

        if address < 0x8000:
            if self.booting:
                if address < 256:
                    raise RuntimeError("Attempt to write into boot ROM")
            self.cartridge.rom[address] = value
        elif address < 0xa000:
            self.display.ram[address-0x8000] = value
        elif address < 0xc000:
            self.ram[address-0xa000] = value

    def get16(self, address):
        return self[address, 2]

    def set16(self, address, value):
        assert(value <= 0xffff)
        value = [(value & 0xff00) >> 16, value & 0xff]
        self[address] = value
