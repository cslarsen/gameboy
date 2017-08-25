#! /usr/bin/env python
# -*- encoding: utf-8 -*-

"""
A Gameboy Emulator.

Implementation notes:

    * On power up, all RAM is set to random values. This is how a real Gameboy
    works, and I want to emulate that (e.g., custom made programs will have to
    clear out memory first. I'd like this emulator to behave like that.)
"""

__author__ = "Christian Stigen Larsen"
__copyright__ = "Copyright 2017 Christian Stigen Larsen"
__license__ = "The GNU GPL v3 or later"
__version__ = "0.1"

from cartridge import Cartridge
from cpu import CPU
from display import Display
from gameboy import Gameboy
from memory import MemoryController
from opcodes import opcodes, extended_opcodes, add_0xff00_opcodes

from util import (
    format_hex,
    load_binary,
    make_array,
    make_randomized_array,
    u8_to_signed,
)

__all__ = (
    "add_0xff00_opcodes",
    "Cartridge",
    "CPU",
    "Display",
    "extended_opcodes",
    "format_hex",
    "Gameboy",
    "load_binary",
    "make_array",
    "make_randomized_array",
    "MemoryController",
    "opcodes",
    "u8_to_signed",
)
