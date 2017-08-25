import os
import sys
from disassembler import disassemble
from argparse import ArgumentParser

from __init__ import (
    __copyright__,
    Cartridge,
    Gameboy,
    load_binary,
)

def find_default_boot_rom():
    return os.path.join(os.path.dirname(__file__), "roms", "boot")

def parse_command_line_args():
    p = ArgumentParser(description="A Gameboy Classic emulator", epilog=__copyright__)

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

def log(msg):
    sys.stdout.write("%s\n" % msg)
    sys.stdout.flush()

def wait_enter():
    if sys.version_info.major < 3:
        return raw_input()
    else:
        return input()

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

        print(gameboy)

        while True:
            gameboy.cpu.step()
            if wait_enter().strip().lower() == "q":
                break

        sys.exit(0)

if __name__ == "__main__":
    main()
