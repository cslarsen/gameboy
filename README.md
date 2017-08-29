GameBoy Classic Emulator in Python
==================================

This is my attempt to make a fully working Gameboy emulator from scratch,
without looking at any other implementation.

Status
======

This is *not yet* a working version.

I'm just pushing to this repo as the project proceeds. See the file
[PROGRESS.md](PROGRESS.md) for a few notes.

Usage
=====

To insert a cartridge and start the emulator:

    $ python gameboy cartridge.gb

To disassemble a file:

    $ python gameboy --start-address=0x00 --disassemble=gameboy/roms/boot

Supported Python versions
=========================

Python 2.7, 3.x and pypy with PySDL2 and numpy.

To use with pypy, install PySDL2 and a version of numpy that works:

    $ pypy -m pip install PySDL2
    $ pypy -m pip install git+https://bitbucket.org/pypy/numpy.git

For me, I'm not able to run numpy with pypy, but if I disable SDL2, the
emulated speed is 5 MHz, so it should in theory be possibly to run the emulator
in real time speed. On the same machine, Python 2.7 will emulate at only 0.6
MHz. This is unoptimized code, of course. First make it correct, then make it
fast.

References
==========

  * [Duo's GameBoy Memory Map](http://gameboy.mongenel.com/dmg/asmmemmap.html)
  * [Game Boy™ CPU Manual](http://marc.rawer.de/Gameboy/Docs/GBCPUman.pdf)
  * [Gameboy Bootstrap ROM](http://gbdev.gg8.se/wiki/articles/Gameboy_Bootstrap_ROM)
  * [Gameboy CPU (LR35902) instruction set](http://pastraiser.com/cpu/gameboy/gameboy_opcodes.html)
  * [Gameboy on Wikipedia](https://en.wikipedia.org/wiki/Game_Boy)
  * [GameBoy Programming Info](https://fms.komkon.org/GameBoy/Tech/Software.html)
  * [GameBoy Programming Manual](http://www.chrisantonellis.com/files/gameboy/gb-programming-manual.pdf)
  * [Pan Docs](http://bgb.bircd.org/pandocs.htm#cpuinstructionset)
  * [The Game Boy Project](http://marc.rawer.de/Gameboy/Docs/GBProject.pdf)

License
=======

Copyright 2017 Christian Stigen Larsen  
Distributed under the GNU GPL v3 or later.

The DMG-01 boot ROM in `roms/boot` is owned and copyrighted by Nintendo Co.,
Ltd. You are not allowed to use or redistribute that file outside of this
repository.

GameBoy is a registered trademark of the Nintendo Corporation.
