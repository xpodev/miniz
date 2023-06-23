from miniz.concrete.signature import Signature
from miniz.interfaces.function import IFunctionSignature, IReturnParameter
from miniz.ownership import Owned
from miniz.core import ImplementsType


class ReturnParameter(IReturnParameter):
    def __init__(self, signature: "FunctionSignature", parameter_type: ImplementsType = None):
        super().__init__(owner=signature)
        self.parameter_type = parameter_type


class FunctionSignature(Signature, IFunctionSignature, Owned["Function"]):
    def __init__(self, name: str = None, return_type: ImplementsType = None):
        super().__init__(name)
        Owned.__init__(self)

        self.return_parameter = ReturnParameter(self, return_type)

    def __repr__(self):
        return f"fun{' ' if self.name else ''}{super().__repr__()}: {self.return_type}"
