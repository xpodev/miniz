"""
This module contains the `Function` class, which represents a Z# function.
"""
from miniz.function_signature import FunctionSignature
from miniz.generic.generic_construction import IConstructor
from miniz.scope import Scope
from miniz.signature import Parameter
from miniz.type_system import ImplementsType, Any
from miniz.vm.instruction import Instruction
from utils import NotifyingList


class FunctionBody:
    owner: "Function"
    _instructions: NotifyingList[Instruction] | None

    def __init__(self, owner: "Function"):
        self.owner = owner
        self._instructions = NotifyingList()

        def on_add_instruction(_, inst):
            if not isinstance(inst, Instruction):
                raise TypeError(f"A normal function's body may only contain instructions")
            if isinstance(inst, IConstructor):
                raise TypeError(f"A normal function may not contain generic instructions")

        self._instructions.append += on_add_instruction

    @property
    def has_body(self):
        return self._instructions is not None

    @property
    def instructions(self):
        return self._instructions


class Function:
    """
    Represents a Z# function. This object should not be exposed to the Z# environment.

    Currently, the function's body may be represented by any object, and it depends on the interpreter implementation.
    """

    signature: FunctionSignature
    _body: FunctionBody

    lexical_scope: Scope

    def __init__(self, lexical_scope: Scope | None, name: str = None, return_type: ImplementsType = Any):
        self.signature = FunctionSignature(name, return_type)
        self.lexical_scope = lexical_scope
        self._body = FunctionBody(self)

    @property
    def name(self):
        return self.signature.name

    @name.setter
    def name(self, value: str):
        self.signature.name = value

    @property
    def body(self):
        return self._body

    @property
    def positional_parameters(self):
        return self.signature.positional_parameters

    @property
    def named_parameters(self):
        return self.signature.named_parameters

    @property
    def variadic_positional_parameter(self):
        return self.signature.variadic_positional_parameter

    @variadic_positional_parameter.setter
    def variadic_positional_parameter(self, value: Parameter | None):
        self.signature.variadic_positional_parameter = value

    @property
    def variadic_named_parameter(self):
        return self.signature.variadic_named_parameter

    @variadic_named_parameter.setter
    def variadic_named_parameter(self, value: Parameter | None):
        self.signature.variadic_named_parameter = value

    @property
    def return_type(self):
        return self.signature.return_type

    @return_type.setter
    def return_type(self, value: ImplementsType):
        self.signature.return_type = value

    def __repr__(self):
        return repr(self.signature) + " {}"
