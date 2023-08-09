"""
This module contains the `Function` class, which represents a Z# function.
"""
from miniz.concrete.function_signature import FunctionSignature
from miniz.template.template_construction import IConstructor
from miniz.interfaces.function import IFunction, ILocal, IFunctionBody
from miniz.ownership import Owned
from miniz.concrete.signature import Parameter
from miniz.core import ImplementsType
from miniz.vm.instruction import Instruction
from utils import NotifyingList


class FunctionBody(IFunctionBody):
    _instructions: NotifyingList[Instruction] | None

    def __init__(self, owner: "IFunction"):
        super().__init__(owner=owner)
        self._instructions = NotifyingList()

        def on_add_instruction(_, inst):
            if not isinstance(inst, Instruction):
                raise TypeError(f"A normal function's body may only contain instructions")
            if isinstance(inst, IConstructor):
                raise TypeError(f"A normal function may not contain generic instructions")

        self._instructions.append += on_add_instruction

    @property
    def owner(self):
        return super().owner

    @owner.setter
    def owner(self, value):
        raise TypeError(f"Can't change the owner of a function body.")

    @property
    def instructions(self):
        return self._instructions

    @instructions.deleter
    def instructions(self):
        self._instructions = None


class Local(ILocal):
    name: str
    type: ImplementsType | Parameter

    def __init__(self, name: str, type: ImplementsType | Parameter):
        super().__init__()
        self.name = name
        self.type = type
        self.owner = None

    @property
    def index(self):
        if self.owner is None:
            raise ValueError(f"Local {self} doesn't have an owner")
        return self.owner.locals.index(self)


class Function(IFunction):
    """
    Represents a Z# function. This object should not be exposed to the Z# environment.
    """

    signature: FunctionSignature

    _body: FunctionBody

    _locals: NotifyingList[Local]

    def __init__(self, name: str = None, return_type: ImplementsType = None):
        Owned.__init__(self)

        self.signature = FunctionSignature(name, return_type)
        self.signature.owner = self
        self._body = FunctionBody(self)
        self._locals = NotifyingList()

        def on_add_local(_, local: Local):
            if local.owner is not None:
                raise ValueError(f"Local variable \'{local}\' if already owned by {local.owner}")
            local.owner = self

        def on_remove_local(_, local: Local | int):
            if isinstance(local, int):
                local = self._locals[local]
            local.owner = None

        self._locals.append += on_add_local

        self._locals.remove += on_remove_local
        self._locals.pop += on_remove_local

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
    def locals(self):
        return self._locals

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
