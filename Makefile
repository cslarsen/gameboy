default: run2

run2:
	python2 gameboy

run3:
	python3.3 gameboy

check:
	python2 -m pyflakes gameboy/*.py
