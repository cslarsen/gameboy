"""
Contains code for handling the GameBoy memory.
"""

from util import (
    make_randomized_array,
    make_array,
)

class Memory(object):
    def __init__(self, length_or_data, randomized=False, readonly=False):
        self.readonly = readonly

        if isinstance(length_or_data, int):
            length = length_or_data
            if randomized:
                self.data = make_randomized_array(length)
            else:
                self.data = make_array([0]*length)
        else:
            data = length_or_data
            self.data = make_array(data)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]

    def __setitem__(self, index, value):
        if self.readonly:
            raise RuntimeError("Attempt to write to readonly memory")
        self.data[index] = value

class MemoryController(object):
    def __init__(self, boot_rom, display, cartridge):
        self.display = display
        self.cartridge = cartridge

        self.ram_banks = []
        for n in range(4):
            self.ram_banks.append(Memory(0x2000))

        self.internal_work_ram = Memory(0x4000)
        self.expanded_work_ram = self.ram_banks[0]
        self.fixed_home = boot_rom
        self.home = self.cartridge.rom_bank[1]

        # Make sure memory is mirrored from the start
        for i in range(0xc000, 0xde01):
            self[i] = self[i+0x1000]

    def _memory_map(self, address):
        """Returns (array, offset) that correspond to the given memory mapped
        address."""

        if 0x0000 <= address < 0x4000:
            return self.fixed_home, 0x0000

        if address < 0x8000:
            return self.home, 0x4000

        if address < 0xa000:
            return self.display.ram, 0x8000

        if address < 0xc000:
            return self.expanded_work_ram, 0xa000

        if address <= 0xffff:
            return self.internal_work_ram, 0xc000

        raise RuntimeError("Invalid memory address 0x%x" % address)

    def __getitem__(self, address):
        """Reads one byte from memory."""
        memory, offset = self._memory_map(address)
        return memory[address - offset]

    def __setitem__(self, address, value):
        """Writes one byte to memory."""
        memory, offset = self._memory_map(address)
        memory[address - offset] = value

        # Mirroring of addresses
        if 0xc000 <= address <= 0xde00:
            memory[address + 0x1000 - offset] = value
        elif 0xe000 <= address <= 0xfe00:
            memory[address - 0x1000 - offset] = value


    def get16(self, address):
        # Little-endian
        return u8_to_u16(self[address], self[address+1])

    def set16(self, address, value):
        # Little-endian
        self[address:address+1] = u16_to_u8(value)
