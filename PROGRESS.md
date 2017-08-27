Gameboy Emulator Progress Log
=============================

Writing a Gameboy emulator is supposed to be pretty straight-forward, so I
thought I'd give it a go.

I've decided not to cheat by looking at any other implementation. That way,
when it finally works, it will feel like a much more personal victory.

Day 1
-----

Started off by writing some skeletal Python code for a CPU, display and memory
mapping.

Found a boot ROM online. It comes with a disassembly listing. That way I can
write my own disassembler and check that it works.

Glad I started on the disassembler. Very easy to get the opcode tables wrong.

Got to spend almost six hours on this today. Not much progress, but I like to
go slowly, but steadily. I'll need to finish the disassembler, then add the
rest of the opcodes. When that's done, I should be able to copy the disassembly
code for use in the CPU instruction dispatcher.

Day 2
-----

Added the remaining opcodes needed to disassemble the boot ROM. Made into a
package, added command line options and added a memory controller to perform
memory mapping. Not very elegantly structured code, but that's not important at
this point.

Will now start with an instruction dispatcher that will eventually be able to
run the boot code.

Started on the instruction fetcher, decoder and executor. Added a very simple
step-debugging interface. Will now need to actually implement those opcodes.
This part will consist of reading and understanding the memory layout, the bank
switching, how to update flags and so on. The execution of instructions is
currently badly structured, so I'll have to do a lot by hand. When I understand
it properly, I can abstract this further, reducing code.

Day 3
-----

Continued implementing instructions. I'm very happy with how I separated the
fetch, decode and execute stages.

Restructured the code. Seem to have fixed the memory mapping. At least it's
good enough for now.

Made a very simple debugger and used it to debug CPU instructions.  A few hours
in, I suddenly realized how essential the debugger had come to be.

Jumps and call with return work, meaning loops work. Seems to execute the boot
code correctly, although debugging far out in the code has become overwhelming.

The emulator currently runs at 0.6 MHz, which isn't too bad for unoptimized
Python. *If* that ever becomes an annoyance, I'll whip out C and Cython to nuke
the problem from space.

At the end of the day, there's an invalid memory access that stops progress,
preventing the boot code to finish.

Next up: Get the boot code to run to end. After that, it's time to hook up a 2D
display. My gut feeling is that will uncover new bugs.

Day 4
-----

Had I just spent five more minutes the last time, I'd see that the problem was
a jump that was not interpreted relatively. Fixing that, the program seemed to
run forever. Breaking in the debugger, I saw what was happening: The boot code
was waiting for the next screen frame! That means it's time to implement the
hardware I/O registers.

Started implementing the video display driver. Currently, it just draws
rubbish, but at least something is happening!
