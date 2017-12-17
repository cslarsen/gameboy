#include <stdint.h>

#pragma pack(0)
struct Registers {
  uint16_t pc;
  uint16_t sp;

  uint8_t a;
  uint8_t f;

  uint8_t b;
  uint8_t c;

  uint8_t d;
  uint8_t e;

  uint8_t h;
  uint8_t l;

  uint16_t af() const;
  void af(const uint16_t v);

  uint16_t bc() const;
  void bc(const uint16_t v);

  uint16_t de() const;
  void de(const uint16_t v);

  uint16_t hl() const;
  void hl(const uint16_t v);

  Registers();
};
