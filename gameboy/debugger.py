import sys

from disassembler import disassemble
from util import (
    format_hex,
    load_binary,
    log,
    wait_enter,
)

def parse_number(s):
    if s.startswith("0x"):
        return int(s, 16)
    else:
        return int(s)

def debugger(gameboy):
    log("\nType CTRL+D or Q to quit, H for help.")

    gameboy.cpu.print_registers()

    continue_running = False
    breakpoints = set()
    break_nl = False

    while True:
        try:
            if (not continue_running) or (gameboy.cpu.PC in breakpoints):
                try:
                    pc = gameboy.cpu.PC
                    if break_nl and pc in breakpoints:
                        log("")
                        break_nl = False
                        continue_running = False
                    prefix = "%s@$%0.4x > " % ("break " if pc in breakpoints else
                            "", pc)
                    command = wait_enter(prefix).strip().lower()
                except EOFError:
                    break
            else:
                command = ""

            if command == "":
                try:
                    break_nl = True
                    gameboy.cpu.step(not continue_running)
                    continue
                except Exception as e:
                    log("\n\n*** Exception: %s" % e)
                    continue_running = False

            if command.startswith("q"):
                break

            if command.startswith("c"):
                continue_running = True
                break_nl = True
                continue

            if command.startswith("b"):
                for bp in command.split()[1:]:
                    breakpoints.add(parse_number(bp))

                if len(breakpoints) == 0:
                    log("No breakpoints")
                else:
                    log("Breakpoints: ")
                    for bp in sorted(breakpoints):
                        log("  + $%0.4x" % bp)
                continue

            if command.startswith("h"):
                log("Commands:")
                log("  - Enter for next instruction")
                log("  - Q or CTRL+D quit")
                log("  - R to print registers")
                log("  - C to continue")
                log("  - B <address> stops at PC=address")
                log("  - M <address> shows eight bytes from memory")
                log("All numbers can be entered as decimal or 0x00 hex")
                continue

            if command.startswith("r"):
                gameboy.cpu.print_registers()
                continue

            if command.startswith("m"):
                addr = command.split()
                if len(addr) > 1:
                    addr = parse_number(addr[1])
                    try:
                        raw = gameboy.memory[addr:addr+8]
                        log("%s" % " ".join(map(lambda x: format_hex(x, prefix="0x"),
                            raw)))
                    except IndexError as e:
                        log(e)
                continue

            if command.startswith("l"):
                start = gameboy.cpu.PC
                code = gameboy.cpu.memory[start:start+16]
                try:
                    disassemble(code, start_address=start)
                except IndexError:
                    log("...")
                continue

            log("Unknown command")
        except KeyboardInterrupt:
            log("")
            break_nl = False
            continue_running = False
