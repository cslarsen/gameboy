#include <SDL.h>

#include "error.hpp"
#include "display.hpp"

static bool initialize() {
  static bool run = false;

  if ( !run ) {
    run = true;
    return SDL_Init(SDL_INIT_VIDEO) == 0;
  }

  return true;
}

struct DisplayImpl {
  DisplayImpl();
  ~DisplayImpl();

  SDL_Window *win;
};

DisplayImpl::DisplayImpl()
{
  if ( !initialize() )
    throw Error(SDL_GetError());

  win = SDL_CreateWindow("GameBoy", 100, 100, 640, 480, SDL_WINDOW_SHOWN);

  if ( win == nullptr )
    throw Error(SDL_GetError());
}

DisplayImpl::~DisplayImpl()
{
  SDL_DestroyWindow(win);
  win = nullptr;
}

Display::Display() : pimpl(new DisplayImpl())
{
}

Display::Display(const Display& o) : pimpl(new DisplayImpl(*o.pimpl))
{
}

Display& Display::operator=(const Display& o)
{
  if (this != &o) {
    delete pimpl;
    pimpl = new DisplayImpl(*o.pimpl);
  }
  return *this;
}

Display::~Display()
{
  delete pimpl;
}
