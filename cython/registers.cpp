#include <string.h>
#include "registers.hpp"

Registers::Registers()
{
  memset(this, 0, sizeof(*this));
}

uint16_t Registers::af() const
{
  return *(&a);
}

void Registers::af(const uint16_t v)
{
  *(&a) = v;
}


uint16_t Registers::bc() const
{
  return *(&b);
}

void Registers::bc(const uint16_t v)
{
  *(&b) = v;
}


uint16_t Registers::de() const
{
  return *(&d);
}

void Registers::de(const uint16_t v)
{
  *(&d) = v;
}


uint16_t Registers::hl() const
{
  return *(&h);
}

void Registers::hl(const uint16_t v)
{
  *(&h) = v;
}
