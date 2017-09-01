import argparse
import logging
import os
import sys

from __init__ import __copyright__
from cartridge import Cartridge
from debugger import Debugger
from disassembler import disassemble
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

        if opt.debug:
            Debugger(gameboy).run()
            sys.exit(0)
        else:
            try:
                if opt.skip_boot:
                    # TODO: Set up registers etc.
                    gameboy.cpu.PC = 0x100
                gameboy.cpu.run()
            except KeyboardInterrupt:
                log("Emulated at %.1f MHz" % gameboy.cpu.emulated_MHz)
                raise
            except Exception as e:
                log("\n\n*** Exception: %s" % e)
                gameboy.cpu.print_registers()
                log("")
                raise

if __name__ == "__main__":
    logger = logging.getLogger('my-logger')
    logger.propagate = False

    try:
        main()
    except StopIteration:
        pass
