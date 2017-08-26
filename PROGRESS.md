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

Continuing with the grunt work of actually implementing the instructions. Added
the first working jump instruction. It's very easy, but takes a long time
because I haven't structured the code very well. Maybe I'll just implement an
instruction class so I can put the implementation right there and then. That's
doable now that I have a rough outline of the main stages: fetching, decoding
and executing.

The memory mapping is still a mess, but will be revisited as soon as I have
implemented enough instructions to run the boot code. Then I'll hook up a
2D window for the display, meaning I probably have to delve into how the bus
works. Hopefully I'll see some scrolling pixels!

Got the first loop in the bood ROM to run. It tries to write into read-only
memory at the end, though, so I have to go back and check the memory mapping
again.
