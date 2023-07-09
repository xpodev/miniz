from miniz.interfaces.base import INamed
from miniz.interfaces.execution import ITarget
from miniz.interfaces.signature import ISignature
from miniz.ownership import Owned
from miniz.core import ImplementsType


class IReturnParameter(Owned["IFunctionSignature"]):
    parameter_type: ImplementsType


class IFunctionSignature(ISignature, Owned["IFunction"]):
    return_parameter: IReturnParameter

    @property
    def return_type(self):
        return self.return_parameter.parameter_type

    @return_type.setter
    def return_type(self, value: ImplementsType):
        self.return_parameter.parameter_type = value


class ILocal(ITarget["IFunction"], INamed):
    ...


class IFunctionBody(Owned["IFunction"]):
    ...


class IFunction(Owned["Module"]):
    signature: IFunctionSignature
    locals: list[ILocal]
    body: IFunctionBody | None

    @property
    def name(self):
        return self.signature.name

    @name.setter
    def name(self, value: str):
        self.signature.name = value
