class EmulatorError(Exception):
    pass

class MemoryError(EmulatorError):
    pass

class OpcodeError(EmulatorError):
    pass

class InvalidOpcodeError(OpcodeError):
    pass
