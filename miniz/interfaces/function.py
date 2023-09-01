from miniz.generic.core import IGeneric
from miniz.interfaces.base import INamed
from miniz.interfaces.execution import ITarget
from miniz.interfaces.signature import ISignature
from miniz.ownership import Owned
from miniz.core import TypeProtocol
from miniz.vm.instruction import Instruction


class IReturnParameter(Owned["IFunctionSignature"]):
    parameter_type: TypeProtocol


class IFunctionSignature(ISignature, Owned["IFunction"]):
    return_parameter: IReturnParameter

    @property
    def return_type(self):
        return self.return_parameter.parameter_type

    @return_type.setter
    def return_type(self, value: TypeProtocol):
        self.return_parameter.parameter_type = value


class ILocal(ITarget["IFunction"], INamed):
    type: TypeProtocol


class IFunctionBody(Owned["IFunction"]):
    instructions: list[Instruction] | None

    @property
    def has_body(self) -> bool:
        return self.instructions is not None


class IFunction(Owned["Module"], IGeneric):
    signature: IFunctionSignature
    locals: list[ILocal]
    body: IFunctionBody | None

    @property
    def name(self):
        return self.signature.name

    @name.setter
    def name(self, value: str):
        self.signature.name = value
