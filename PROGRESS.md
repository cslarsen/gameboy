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

Found a boot ROM online. Since it comes with a disassembled listing, I'll write
my own disassembler. That way I can check that it actually works.
