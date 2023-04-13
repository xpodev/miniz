from dataclasses import dataclass
from typing import Callable

from miniz.function import Function
from miniz.generic.signature import GenericParameter
from miniz.oop import Field
from miniz.signature import Parameter
from miniz.type_system import ObjectProtocol
from miniz.vm.instruction import Instruction

_cfg = {
    "slots": True,
    "unsafe_hash": True
}


@dataclass(**_cfg)
class CallNative(Instruction):
    callee: Callable


@dataclass(**_cfg)
class Call(Instruction):
    """
    The `call` instruction.

    if the `callee` argument is `None`, it is popped from the top of the stack.
    """
    callee: Function | None


@dataclass(**_cfg)
class Return(Instruction):
    """
    The `return` instruction.

    if `has_return_value` is `True`, the top of the stack is copied to the previous frame.
    """
    has_return_value: bool


@dataclass(**_cfg)
class DynamicNameLookup(Instruction):
    name: str


@dataclass(**_cfg)
class LoadArgument(Instruction):
    parameter: Parameter | GenericParameter | int


@dataclass(**_cfg)
class LoadField(Instruction):
    field: Field


@dataclass(**_cfg)
class LoadObject(Instruction):
    object: ObjectProtocol


@dataclass(**_cfg)
class SetArgument(Instruction):
    parameter: Parameter


@dataclass(**_cfg)
class SetField(Instruction):
    field: Field


@dataclass(**_cfg)
class TypeOf(Instruction):
    """
    Why is this an instruction?
    Because getting the type of object is fundamental in the MiniZ type system
    """


class EndOfProgram(Instruction):
    ...
