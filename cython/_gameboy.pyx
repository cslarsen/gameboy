# distutils: language = c++
# cython: c_string_type=unicode, c_string_encoding=utf8

from libc.stdint cimport uint8_t, uint16_t
from libcpp cimport bool
from libcpp.string cimport string

cdef extern from "display.hpp":
    cdef cppclass CDisplay "Display":
        CDisplay()

cdef extern from "cpu.hpp":
    cdef cppclass CRegisters "Registers":
        uint16_t pc
        uint16_t sp
        uint8_t a
        uint8_t f
        uint8_t b
        uint8_t c
        uint8_t d
        uint8_t e
        uint8_t h
        uint8_t l

        uint16_t af() const
        void af(const uint16_t v)

        uint16_t bc() const
        void bc(const uint16_t v)

        uint16_t de() const
        void de(const uint16_t v)

        uint16_t hl() const
        void hl(const uint16_t v)

        Registers()


    cdef cppclass CCPU "CPU":
        CRegisters reg
        CCPU()

cdef class CPU(object):
    cdef CCPU _cpu

    def __cinit__(self):
        self._cpu = CCPU()

    @property
    def pc(self):
        return self._cpu.reg.pc

    @pc.setter
    def pc(self, uint16_t value):
        self._cpu.reg.pc = value

cdef class Display(object):
    cdef CDisplay _display

    def __cinit__(self):
        self._display = CDisplay()

