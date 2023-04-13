from miniz.signature import Signature
from miniz.type_system import ImplementsType, Any


class FunctionSignature(Signature):
    return_type: ImplementsType

    def __init__(self, name: str = None, return_type: ImplementsType = Any):
        super().__init__(name)

        self.return_type = return_type

    def __repr__(self):
        return f"fun{' ' if self.name else ''}{super().__repr__()}: {self.return_type}"
