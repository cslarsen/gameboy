GAME := ~/games/test.gb

default: run2

run2:
	python2 gameboy

run3:
	python3.3 gameboy

run:
	python gameboy $(GAME)

run-skip:
	python gameboy $(GAME) --skip-boot

run-pypy:
	pypy gameboy $(GAME)

debug:
	python gameboy --debug $(GAME)

profile:
	python -m cProfile gameboy/__main__.py $(GAME)

disasm:
	python gameboy --start-address=0x000 --disassemble=boot

check:
	python2 -m pyflakes gameboy/*.py
