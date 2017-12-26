#include <stdexcept>

class Error : std::runtime_error {
public:
  Error(const char* s) : std::runtime_error(s) {
  }
};
