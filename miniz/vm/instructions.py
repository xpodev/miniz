from dataclasses import dataclass
from typing import Callable

from miniz.concrete.function import Function, Local
from miniz.template.signature import ParameterTemplate
from miniz.concrete.oop import Field, Method
from miniz.concrete.signature import Parameter
from miniz.core import ObjectProtocol
from miniz.vm.instruction import Instruction

_cfg = {
    "slots": True,
    "unsafe_hash": True
}


@dataclass(**_cfg)
class CallNative(Instruction):
    callee: Callable

    op_code = "call-native"
    operands = ["callee"]


@dataclass(**_cfg)
class Call(Instruction):
    """
    The `call` instruction.

    if the `callee` argument is `None`, it is popped from the top of the stack.
    """
    callee: Function | None

    op_code = "call"
    operands = ["callee"]


@dataclass(**_cfg)
class CreateInstance(Instruction):
    constructor: Method

    op_code = "create-instance"
    operands = ["constructor"]


# @dataclass(**_cfg)
# class DynamicNameLookup(Instruction):
#     name: str


class DuplicateTop(Instruction):
    op_code = "duplicate-top"


@dataclass(**_cfg)
class Jump(Instruction):
    target: Instruction

    op_code = "jump"
    operands = ["target"]


@dataclass(**_cfg)
class JumpIfFalse(Instruction):
    target: Instruction

    op_code = "jump-if-false"
    operands = ["target"]


@dataclass(**_cfg)
class JumpIfTrue(Instruction):
    target: Instruction

    op_code = "jump-if-true"
    operands = ["target"]


@dataclass(**_cfg)
class LoadArgument(Instruction):
    parameter: Parameter | ParameterTemplate | int

    op_code = "load-argument"
    operands = ["parameter"]


@dataclass(**_cfg)
class LoadField(Instruction):
    field: Field

    op_code = "load-field"
    operands = ["field"]


@dataclass(**_cfg)
class LoadLocal(Instruction):
    local: Local

    op_code = "load-local"
    operands = ["local"]


@dataclass(**_cfg)
class LoadObject(Instruction):
    object: ObjectProtocol

    op_code = "load-object"
    operands = ["object"]

    @classmethod
    def true(cls):
        from miniz.type_system import Boolean
        return cls(Boolean.TrueInstance)

    @classmethod
    def false(cls):
        from miniz.type_system import Boolean
        return cls(Boolean.FalseInstance)

    @classmethod
    def null(cls):
        from miniz.type_system import Null
        return cls(Null.NullInstance)

    @classmethod
    def unit(cls):
        from miniz.type_system import Unit
        return cls(Unit.UnitInstance)


class NoOperation(Instruction):
    op_code = "nop"


class Return(Instruction):
    """
    The `return` instruction.
    """

    op_code = "return"


@dataclass(**_cfg)
class SetArgument(Instruction):
    parameter: Parameter

    op_code = "set-argument"
    operands = ["parameter"]


@dataclass(**_cfg)
class SetField(Instruction):
    field: Field

    op_code = "set-field"
    operands = ["field"]


@dataclass(**_cfg)
class SetLocal(Instruction):
    local: Local

    op_code = "set-local"
    operands = ["local"]


class TypeOf(Instruction):
    """
    Why is this an instruction?
    Because getting the type of object is fundamental in the MiniZ type system
    """

    op_code = "typeof"
