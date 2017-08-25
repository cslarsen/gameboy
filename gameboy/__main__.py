import os
import sys
import argparse

from __init__ import __copyright__
from cartridge import Cartridge
from disassembler import disassemble
from gameboy import Gameboy
from util import load_binary, log, wait_enter

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
        log("... %d bytes" % len(binary))
        cartridge = Cartridge(binary)

        log("Booting Gameboy")
        gameboy = Gameboy(cartridge, boot)

        log("\nType CTRL+D or Q to quit, H for help.")
        command = ""
        gameboy.cpu.print_registers()

        while True:
            try:
                command = wait_enter("> ").strip().lower()
            except EOFError:
                break

            if command.startswith("q"):
                break
            elif command.startswith("h"):
                log("CTRL+D or Q to quit")
                log("ENTER for next instruction")
                log("R to print registers")
                log("Registers are shown AFTER executiong the shown instruction")
            elif command.startswith("r"):
                gameboy.cpu.print_registers()
            else:
                gameboy.cpu.step()

        sys.exit(0)

if __name__ == "__main__":
    main()
