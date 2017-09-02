import argparse
import logging
import os
import sys

from __init__ import __copyright__
from cartridge import Cartridge
from debugger import Debugger
from disassembler import disassemble
from errors import EmulatorError
from gameboy import Gameboy
from util import load_binary, log

def find_default_boot_rom():
    return os.path.join(os.path.dirname(__file__), "roms", "boot")

def parse_command_line_args():
    p = argparse.ArgumentParser(
            description="A Gameboy Classic emulator",
            epilog=__copyright__)

    p.add_argument("-d", "--disassemble", metavar="FILE", default=None,
            help="Disassemble binary file. Specify 'boot' for boot ROM")

    p.add_argument("--start-address", default=0, metavar="ADDRESS",
            help="Start address when disassembling")

    p.add_argument("cartridge", type=str, metavar=("FILE",), default=None,
            nargs="?",
            help="Which cartridge to insert before booting the Gameboy")

    p.add_argument("--boot-rom", type=str, metavar="FILE",
            default=find_default_boot_rom(),
            help="Which boot ROM to use when powering up")

    p.add_argument("--debug", default=False, action="store_true",
            help="Perform interactive step debugging")

    p.add_argument("--no-display", default=False, action="store_true",
            help="Do not open a 2D display window")

    p.add_argument("--zoom", default=1, type=int,
            help="Zoom factor for display")

    p.add_argument("--skip-boot", default=False, action="store_true",
            help="Skips the boot code")

    opt = p.parse_args()

    if isinstance(opt.start_address, str):
        ishex = opt.start_address.startswith(("0x", "$"))
        try:
            opt.start_address = int(opt.start_address, 16 if ishex else 10)
        except ValueError:
            print("Invalid start address: %s" % opt.start_address)
            sys.exit(1)

    if opt.cartridge is None and opt.disassemble is None:
        p.print_help()
        sys.exit(1)

    return opt

def main():
    opt = parse_command_line_args()

    if opt.disassemble is not None:
        if opt.disassemble == "boot":
            opt.disassemble = opt.boot_rom

        binary = load_binary(opt.disassemble)
        print("Disassembly of %s\n" % os.path.relpath(opt.disassemble))
        disassemble(binary, opt.start_address)
        sys.exit(0)

    if opt.cartridge is not None:
        log("Loading boot ROM from %s" % os.path.relpath(opt.boot_rom))
        boot = load_binary(opt.boot_rom)

        log("Loading cartridge from %s" % os.path.relpath(opt.cartridge))
        binary = load_binary(opt.cartridge)
        cartridge = Cartridge(binary)
        log(cartridge)

        log("Booting Gameboy")
        gameboy = Gameboy(cartridge, boot, no_display=opt.no_display,
                zoom=opt.zoom)

        if opt.skip_boot:
            # Set up registers and so on in the state it would be in after
            # completing the Nintendo boot code.

            gameboy.cpu.AF = 0x0001
            gameboy.cpu.BC = 0x0013
            gameboy.cpu.DE = 0x00d8
            gameboy.cpu.HL = 0x014f
            gameboy.cpu.PC = 0x0100
            gameboy.cpu.SP = 0xfffe

            gameboy.memory.boot_rom_active = False

            gameboy.memory[0xff05] = 0x00 # TIMA
            gameboy.memory[0xff06] = 0x00 # TMA
            gameboy.memory[0xff07] = 0x00 # TAC
            gameboy.memory[0xff10] = 0x80 # NR10
            gameboy.memory[0xff11] = 0xbf # NR11
            gameboy.memory[0xff12] = 0xf4 # NR12
            gameboy.memory[0xff14] = 0xbf # NR14
            gameboy.memory[0xff16] = 0x3f # NR21
            gameboy.memory[0xff17] = 0x00 # NR22
            gameboy.memory[0xff19] = 0xbf # NR24
            gameboy.memory[0xff1a] = 0x7f # NR30
            gameboy.memory[0xff1b] = 0xff # NR31
            gameboy.memory[0xff1c] = 0x9f # NR32
            gameboy.memory[0xff1e] = 0xbf # NR33
            gameboy.memory[0xff20] = 0xff # NR41
            gameboy.memory[0xff21] = 0x00 # NR42
            gameboy.memory[0xff22] = 0x00 # NR43
            gameboy.memory[0xff23] = 0xbf # NR30
            gameboy.memory[0xff24] = 0x77 # NR50
            gameboy.memory[0xff25] = 0xf3 # NR51
            gameboy.memory[0xff26] = 0xf1 # GB
            gameboy.memory[0xff40] = 0x91 # LCDC
            gameboy.memory[0xff42] = 0x00 # SCY
            gameboy.memory[0xff43] = 0x00 # SCX
            gameboy.memory[0xff45] = 0x00 # LYC
            gameboy.memory[0xff47] = 0xfc # BGP
            gameboy.memory[0xff48] = 0xff # OBP0
            gameboy.memory[0xff49] = 0xff # OBP1
            gameboy.memory[0xff4a] = 0x00 # WY
            gameboy.memory[0xff4b] = 0x00 # WX
            gameboy.memory[0xffff] = 0x00 # IE

        if opt.debug:
            Debugger(gameboy).run()
            sys.exit(0)
        else:
            try:
                gameboy.cpu.run()
            except EmulatorError as e:
                log("\n** Exception: %s" % str(e).strip())
                Debugger(gameboy).run()
            except Exception as e:
                log("\n** Exception: %s" % str(e).strip())
                gameboy.cpu.print_registers()
                log("")
                raise

if __name__ == "__main__":
    logger = logging.getLogger('my-logger')
    logger.propagate = False

    try:
        main()
    except (KeyboardInterrupt, StopIteration):
        pass
