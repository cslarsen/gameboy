#include <SDL.h>

#include "display.hpp"

static bool initialize() {
  static bool initialized = false;

  if ( !initialized ) {
    initialized = true;
    if ( SDL_Init(SDL_INIT_VIDEO) != 0 ) {
      puts(SDL_GetError());
      return false;
    }
  }

  return true;
}

struct DisplayImpl {
  SDL_Window *win;

  DisplayImpl() {
    initialize();

    win = SDL_CreateWindow("GameBoy", 100, 100, 640, 480, SDL_WINDOW_SHOWN);
    if (win == nullptr) {
      puts(SDL_GetError());
    }
  }
};

Display::Display() : pimpl(new DisplayImpl) {
}

Display::Display(const Display& o) : pimpl(new DisplayImpl(*o.pimpl)) {
}

Display& Display::operator=(const Display& o) {
  if (this != &o) {
    delete pimpl;
    pimpl = new DisplayImpl(*o.pimpl);
  }
  return *this;
}

Display::~Display() {
  delete pimpl;
}
