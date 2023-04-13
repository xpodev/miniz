class Instruction:
    """
    The base class for all instructions executable by the MiniZ CTI (compile-time interpreter).

    The VM is a stack machine. But not all values go through the stack.
    """

    index: int
