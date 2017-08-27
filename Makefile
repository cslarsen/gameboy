default: run2

run2:
	python2 gameboy

run3:
	python3.3 gameboy

run:
	python gameboy ~/games/*.gb

disasm:
	python gameboy --start-address=0x000 --disassemble=boot

check:
	python2 -m pyflakes gameboy/*.py
