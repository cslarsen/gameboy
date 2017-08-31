import sys

from disassembler import disassemble
from util import (
    format_hex,
    load_binary,
    log,
    wait_enter,
)

def number(args, index, default):
    try:
        return parse_number(args[index])
    except:
        return default

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

    def step(self):
        self.newline_on_break = True
        self.gameboy.cpu.step()

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
            self.step()
        elif c == "b":
            try:
                self.set_breakpoints(*map(parse_number, args))
            except ValueError as e:
                log(e)
        elif c == "c":
            run_to = number(args, 0, None)
            while True:
                self.step()
                if self.PC == run_to or self.PC in self.breakpoints:
                    break
        elif c == "r":
            self.gameboy.cpu.print_registers()
        elif c == "h":
            self.print_help()
        elif c == "m":
            start = number(args, 0, 0)
            end = number(args, 1, start+8)
            self.dump_memory(start, end)
        elif c == "z":
            addr = number(args, 0, None)
            val = number(args, 1, 0)
            if addr is not None:
                self.gameboy.memory[addr] = val
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

    def dump_memory(self, start, stop):
        try:
            raw = []
            addr = start
            for n in range(0, stop-start):
                # Don't read by slice. We want to get the I/O data as well.
                raw.append(self.gameboy.memory[start+n])
                if len(raw) == 8:
                    log("$%0.4x:  %s" % (addr, " ".join(map(lambda x: format_hex(x,
                        prefix="0x"), raw))))
                    addr += 8
                    raw = []
            if len(raw) > 0:
                log("$%0.4x:  %s" % (addr, " ".join(map(lambda x: format_hex(x,
                    prefix="0x"), raw))))
        except IndexError as e:
            log(e)

    def disassemble(self, address, length=16):
        code = []
        for n in range(address, address+length):
            code.append(self.gameboy.cpu.memory[n])
        try:
            disassemble(code, start_address=address)
        except IndexError:
            log("...")

    def print_help(self):
        log("COMMANDS")
        log("  b [address / -address]: list, add and remove breakpoints")
        log("  c [address]: continue running until ctrl+c, breakpoint or address")
        log("  enter: repeat last command")
        log("  l [address] [length]: disassemble code at address and length bytes out")
        log("  m address: show eight raw bytes in memory")
        log("  q or ctrl+d: quit")
        log("  r: show registers")
        log("  s: step debug (run next instruction)")
        log("  z address [value]: Set memory location to value (default zero)")
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
