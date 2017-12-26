CXXFLAGS := -W -Wall -Og --std=c++11 -xc++
TARGETS := _gameboy.so

PYFLAGS := $(shell python-config --includes --libs)
SDLFLAGS := $(shell sdl2-config --cflags --libs)

all: $(TARGETS)

%.cpp: %.pyx
	cythonize $<

_gameboy.so: _gameboy.cpp cpu.cpp registers.cpp display.cpp
	$(CXX) $(CXXFLAGS) $(PYFLAGS) $(SDLFLAGS) $^ -fPIC -shared -o _gameboy.so

clean:
	rm -f $(TARGETS)
