import typing

from miniz.concrete.function_signature import FunctionSignature
from miniz.concrete.signature import Parameter
from miniz.core import TypeProtocol
from miniz.generic.core import GenericInstance
from miniz.interfaces.signature import IParameter

if typing.TYPE_CHECKING:
    from miniz.interfaces.function import IFunction


class GenericFunctionInstanceType(TypeProtocol):
    _instance: "GenericFunctionInstance"

    def __init__(self, instance: "GenericFunctionInstance"):
        self._instance = instance

    def assignable_from(self, source: "TypeProtocol") -> bool:
        ...

    def assignable_to(self, target: "TypeProtocol") -> bool:
        ...


class GenericFunctionInstance(GenericInstance):
    def __init__(self, origin: "IFunction", arguments: dict[IParameter, TypeProtocol]):
        super().__init__(origin, arguments)

        self.runtime_type = GenericFunctionInstanceType(self)
        self.signature = FunctionSignature(origin.name)

        for parameter in self.origin.signature.positional_parameters:
            self.signature.positional_parameters.append(Parameter(parameter.name, arguments.get(parameter.parameter_type, parameter.parameter_type)))

        self.signature.return_type = arguments.get(self.origin.signature.return_type, self.origin.signature.return_type)
