CXXFLAGS := -W -Wall -Og --std=c++11 -xc++
TARGETS := _gameboy.so

all: $(TARGETS)

%.cpp: %.pyx
	cythonize $<

_gameboy.so: _gameboy.cpp cpu.cpp registers.cpp
	$(CXX) $(CXXFLAGS) $(shell python-config --includes --libs) $^ -fPIC -shared -o _gameboy.so

clean:
	rm -f $(TARGETS)
