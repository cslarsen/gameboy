#include <stdint.h>

#include "registers.hpp"

class CPU {
public:
  CPU();
  ~CPU();

  Registers reg;
};
