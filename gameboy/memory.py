"""
Contains code for handling the GameBoy memory.

Unlike other emulators, we randomize internal RAM on power-up, just like a real
GameBoy. (TODO: Add a command-line flag to initialize to zero instead)

The reason is that real GameBoy programs must clear out the memory, not relying
on the RAM being zero initialized. This will then serve as a litmus test for
non-official GameBoy programs. Good if you intend to run the program on a real
GameBoy at some point.

TODO: Provide a better mapping of special memory locations such as 0xff44.
"""

from util import (
    log,
    make_array,
    make_randomized_array,
    u16_to_u8,
    u8_to_u16,
)

from errors import (
    MemoryError,
)

class Memory(object):
    def __init__(self, length_or_data, randomized=False, readonly=False,
            name=None, offset=0x0):
        """
        Args:
            length_or_data: Number of bytes or initialization data.
            randomized: Randomize all values.
            readonly: Prevent writes to memory.
            name: Optional name of the memory area.
            offset: Absolute start address in the GameBoy.
        """
        self.readonly = readonly
        self.name = name
        self.offset = offset

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
        try:
            return self.data[index]
        except IndexError:
            raise MemoryError("Out of range address 0x%0.4x for %r" % (index,
                self.name))

    def __setitem__(self, index, value):
        if self.readonly:
            raise MemoryError("%r: Attempt to write to readonly memory at $%0.4x"
                    % (self.name, index))
        self.data[index] = value % 0x100

class MemoryController(object):
    def __init__(self, boot_rom, display, cartridge):
        self.boot_rom = Memory(boot_rom, readonly=True, name="Nintendo boot ROM")
        self.display = display
        self.cartridge = cartridge

        self.ram_banks = []
        for n in range(4):
            self.ram_banks.append(Memory(0x2000, randomized=True,
                name="RAM bank %d" % n))

        self.internal_work_ram = Memory(0x4000, randomized=True,
                name="Internal work RAM")
        self.expanded_work_ram = self.ram_banks[0]
        self.fixed_home = self.cartridge.rom_bank[0]
        self.home = self.cartridge.rom_bank[1]

        self.boot_rom_active = True

        # Make sure memory is mirrored from the start
        for i in range(0xc000, 0xde01):
            self[i] = self[i+0x1000]

    def _memory_map(self, address):
        """Returns (array, offset) that correspond to the given memory mapped
        address."""

        if 0x0 <= address < 0x0100 and self.boot_rom_active:
            # Contains a few reserved memory locations. However, on power-up,
            # this are will refer to the boot ROM. After boot-up, this area
            # will be usable again.
            return self.boot_rom, 0x0

        if 0x0 <= address < 0x4000:
            return self.fixed_home, 0x0

        if address < 0x8000:
            return self.home, 0x4000

        if address < 0xa000:
            return self.display.ram, 0x8000

        if address < 0xc000:
            return self.expanded_work_ram, 0xa000

        if address <= 0xffff:
            return self.internal_work_ram, 0xc000

        # Don't raise exception. Instead figure out how a real Gameboy would
        # handle an invalid memory location.
        return None, None

        #raise MemoryError("Invalid memory address 0x%x" % address)

    def __getitem__(self, address):
        """Reads one byte from memory."""
        # Intercept a few I/O locations for now, restructure later.
        if address == 0xff40:
            return self.display.LCDCONT
        if address == 0xff42:
            return self.display.SCY
        if address == 0xff43:
            return self.display.SCX
        if address == 0xff44:
            return self.display.LY
        if address == 0xff47:
            return self.display.BGPAL

        memory, offset = self._memory_map(address)

        if memory is None and offset is None:
            # Bad access
            return 0

        if address < offset:
            raise MemoryError("%r: Adress 0x%0.4x less than offset 0x%0.4x" % (
                memory.name, address, offset))
        if (address - offset) < len(memory):
            return memory[address - offset]
        else:
            raise MemoryError(
"%r: Invalid address=0x%0.4x - offset=0x%0.4x = 0x%0.4x, length 0x%0.4x" % (
    memory.name, address, offset, address - offset, len(memory)))

    def __setitem__(self, address, value):
        """Writes one byte to memory."""
        if address == 0xff40:
            self.display.LCDCONT = value
            return
        if address == 0xff42:
            self.display.SCY = value
            return
        if address == 0xff43:
            self.display.SCX = value
            return
        if address == 0xff44:
            # Any write to this location will reset LY
            self.display.LY = 0
            return
        if address == 0xff47:
            self.display.BGPAL = value
            return
        if address == 0xff50:
            if self.boot_rom_active:
                log("DMG boot ROM turned off!")
                self.boot_rom_active = False
            # Do not return here

        if address < 0x8000:
            try:
                # Write to ROM is a request for bank-switching
                #log("Switching home to ROM bank %d" % value)
                value = (value % self.cartridge.rom_banks)
                if value == 0:
                    value = 1
                self.home = self.cartridge.rom_bank[value]
                return
            except IndexError:
                log("Warning: Invalid ROM bank $%0.2x, ignoring" % value)
                return

        memory, offset = self._memory_map(address)

        if memory is None and offset is None:
            # Bad memory access
            return

        memory[address - offset] = value

        # Mirroring of addresses
        if 0xc000 <= address <= 0xde00:
            memory[address + 0x1000 - offset] = value % 0x100
        elif 0xe000 <= address <= 0xfe00:
            memory[address - 0x1000 - offset] = value % 0x100

    def get16(self, address):
        return u8_to_u16(self[address+1], self[address])

    def set16(self, address, value):
        hi, lo = u16_to_u8(value)
        self[address+1] = hi
        self[address] = lo
