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
