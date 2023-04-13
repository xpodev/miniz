from typing import Callable

from miniz.function_signature import FunctionSignature
from miniz.generic.generic_construction import IConstructor, recursive_resolve
from miniz.generic.signature import GenericSignature, GenericParameter
from miniz.signature import Parameter
from miniz.type_system import ImplementsType, Any, ObjectProtocol


class GenericFunctionSignature(GenericSignature):
    return_type: ImplementsType | GenericParameter | Parameter

    def __init__(self, name: str = None, return_type: ImplementsType | Parameter = Any):
        super().__init__(name)

        self.return_type = return_type

    def construct(
            self,
            args: dict[Parameter | GenericParameter, ObjectProtocol],
            factory: Callable[[str], FunctionSignature] = None,
            generic_factory: Callable[[str], "GenericFunctionSignature"] = None
    ) -> "FunctionSignature | GenericFunctionSignature":
        result = super().construct(args, factory or FunctionSignature, generic_factory or GenericFunctionSignature)

        return_type = recursive_resolve(args, self.return_type)
        if isinstance(return_type, IConstructor):
            return_type = return_type.construct(args)

        result.return_type = return_type

        return result

    def __repr__(self):
        return f"fun{' ' if self.name else ''}{super().__repr__()}: {self.return_type.name if isinstance(self.return_type, Parameter) else self.return_type}"


if __name__ == '__main__':
    from miniz.type_system import Type, Boolean

    T = Parameter("T", Type)

    generic = GenericFunctionSignature("foo", T)

    value = GenericParameter("value", T)

    generic.positional_parameters.append(value)

    print(generic)

    concrete = generic.construct({T: Boolean})

    print(concrete)
