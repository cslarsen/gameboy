import sys

from disassembler import disassemble
from util import (
    format_hex,
    load_binary,
    log,
    wait_enter,
)

def parse_number(s):
    sign = 1
    if s.startswith("-"):
        s = s[1:]
        sign = -1

    if s.startswith("$"):
        return sign*int(s[1:], 16)
    elif s.startswith("0x"):
        return sign*int(s, 16)
    elif s.startswith("0b"):
        return sign*int(s, 2)
    else:
        return sign*int(s, 10)

class Debugger(object):
    def __init__(self, gameboy):
        self.breakpoints = set()
        self.gameboy = gameboy
        self.newline_on_break = False
        self.quit = False
        self.previous_command = (None, None)

    @property
    def PC(self):
        return self.gameboy.cpu.PC

    def read_command(self):
        cmd = ""
        args = []

        try:
            prefix = "@$%0.4x > " % self.PC
            s = wait_enter(prefix).strip().lower().split()
            if len(s) > 0:
                cmd = s[0]
            if len(s) > 1:
                args = s[1:]
        except EOFError:
            return "q", None

        return cmd, args

    def step(self, trace):
        self.newline_on_break = True
        self.gameboy.cpu.step(trace)

    def dispatch(self, command, args):
        if command == None:
            return

        if command == "": # ENTER
            self.dispatch(*self.previous_command)
            return

        c = command[0]

        if c == "q":
            self.quit = True
        elif c == "s":
            self.step(True)
        elif c == "b":
            try:
                self.set_breakpoints(*map(parse_number, args))
            except ValueError as e:
                log(e)
        elif c == "c":
            while True:
                self.step(False)
                if self.PC in self.breakpoints:
                    break
        elif c == "r":
            self.gameboy.cpu.print_registers()
        elif c == "h":
            self.print_help()
        elif c == "m":
            try:
                self.dump_memory(*map(parse_number, args))
            except ValueError as e:
                log(e)
        elif c == "l":
            address = self.PC
            length = 16
            if len(args) > 0:
                try:
                    address = parse_number(args[0])
                except ValueError as e:
                    log(e)
                    return

            if len(args) > 1:
                try:
                    length = parse_number(args[1])
                except ValueError as e:
                    log(e)
                    return
            self.disassemble(address, length)
        else:
            log("Unknown command: %s" % command)
            return

        self.previous_command = (command, args)

    def set_breakpoints(self, *breakpoints):
        if len(breakpoints) == 0:
            log("Breakpoints: ")
            for bp in sorted(self.breakpoints):
                log("  $%0.4x" % bp)
            return

        for bp in breakpoints:
            if bp < 0 and bp in breakpoints:
                self.breakpoints.remove(-bp)
                log("Removed %s" % format_hex(-bp))
            else:
                self.breakpoints.add(bp)
                log("Breaking on %s" % format_hex(bp))

    def dump_memory(self, *addresses):
        for addr in addresses:
            try:
                raw = self.gameboy.memory[addr:addr+8]
                log("%s:  %s" % (addr, " ".join(map(lambda x: format_hex(x,
                    prefix="0x"), raw))))
            except IndexError as e:
                log(e)

    def disassemble(self, address, length=16):
        code = self.gameboy.cpu.memory[address:address+length]
        try:
            disassemble(code, start_address=address)
        except IndexError:
            log("...")

    def print_help(self):
        log("COMMANDS")
        log("  b [address / -address]: list, add and remove breakpoints")
        log("  c: continue running until ctrl+c or breakpoint")
        log("  enter: repeat last command")
        log("  l [address] [length]: disassemble code at address and length   bytes out")
        log("  m address: show eight raw bytes in memory")
        log("  q or ctrl+d: quit")
        log("  r: show registers")
        log("  s: step debug (run next instruction)")
        log("")
        log("All numbers can be written in decimal, binary or hexadecimal: 123 0x7b $7b")
        log("0b1111011")

    def run(self):
        log("\nType CTRL+D or Q to quit, H for help.")

        while not self.quit:
            command, args = self.read_command()
            try:
                self.dispatch(command, args)
            except KeyboardInterrupt:
                self.newline_on_break = True
            except RuntimeError as e:
                log("\n*** Exception: %s\n" % e)
