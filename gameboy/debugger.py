import sys

from disassembler import disassemble

from util import (
    format_hex,
    load_binary,
    log,
    wait_enter,
)

def debugger(gameboy):
    log("\nType CTRL+D or Q to quit, H for help.")

    gameboy.cpu.print_registers()

    continue_running = False
    breakpoints = set()

    while True:
        if (not continue_running) or (gameboy.cpu.PC in
                breakpoints):
            try:
                if gameboy.cpu.PC in breakpoints:
                    log("\nbreak")
                command = wait_enter("> ").strip().lower()
            except EOFError:
                break
        else:
            command = ""

        if command.startswith("q"):
            break
        elif command.startswith("c"):
            continue_running = True
        elif command.startswith("b"):
            for bp in command.split()[1:]:
                if bp.startswith("0x"):
                    bp = int(bp, 16)
                else:
                    bp = int(bp)
                breakpoints.add(bp)

            if len(breakpoints) == 0:
                log("No breakpoints")
            else:
                log("Breakpoints: ")
                for bp in sorted(breakpoints):
                    log("  + $%0.4x" % bp)
        elif command.startswith("h"):
            log("Commands:")
            log("  - Enter for next instruction")
            log("  - Q or CTRL+D quit")
            log("  - R to print registers")
            log("  - C to continue")
            log("  - B <address> stops at PC=address")
        elif command.startswith("r"):
            gameboy.cpu.print_registers()
        elif command.strip() == "":
            try:
                gameboy.cpu.step(not continue_running)
                if continue_running:
                    sys.stdout.write("%-78s\r" % gameboy.cpu.prev_inst)
                    sys.stdout.flush()
            except Exception as e:
                log("\n\n*** Exception: %s" % e)
        elif command.startswith("l"):
            start = gameboy.cpu.PC
            code = gameboy.cpu.memory[start:start+16]
            try:
                disassemble(code, start_address=start)
            except IndexError:
                log("...")
        else:
            log("Unknown command")
