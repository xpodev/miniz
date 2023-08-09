from dataclasses import dataclass, Field

from miniz.concrete.function import Function
from miniz.template.function import FunctionTemplate
from miniz.template.generic_construction import IConstructor
from miniz.template.oop import FieldTemplate
from miniz.template.signature import ParameterTemplate
from miniz.concrete.signature import Parameter
from miniz.type_system import ObjectProtocol
from miniz.vm.instruction import Instruction

_cfg = {
    "slots": True
}


class GenericInstruction(IConstructor[Instruction]):
    ...


@dataclass(**_cfg)
class Call(GenericInstruction):
    callee: Function | FunctionTemplate
    args: list[ObjectProtocol]
    kwargs: dict[str, ObjectProtocol]


@dataclass(**_cfg)
class Return(GenericInstruction):
    value: ObjectProtocol | None = None


@dataclass(**_cfg)
class DynamicNameLookup(GenericInstruction):
    name: str


@dataclass(**_cfg)
class LoadArgument(GenericInstruction):
    parameter: Parameter | ParameterTemplate


@dataclass(**_cfg)
class LoadField(GenericInstruction):
    field: Field | FieldTemplate
    instance: ObjectProtocol | None


@dataclass(**_cfg)
class LoadObject(GenericInstruction):
    object: ObjectProtocol


@dataclass(**_cfg)
class TypeOf(GenericInstruction):
    """
    Why is this an instruction?
    Because getting the type of object is so fundamental in the MiniZ type system
    """
