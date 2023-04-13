from typing import Callable, TypeVar

from miniz.function import Function, FunctionBody
from miniz.generic.generic_construction import IConstructor
from miniz.generic.function_signature import GenericFunctionSignature
from miniz.generic.signature import GenericParameter
from miniz.scope import Scope
from miniz.signature import Parameter
from miniz.type_system import ImplementsType, Any, ObjectProtocol

_T = TypeVar("_T")
_GenericT = TypeVar("_GenericT")


class GenericFunction(IConstructor[Function]):
    """
    Represents a generic Z# function. This object should not be exposed to the Z# environment.

    Currently, the function's body may be represented by any object, and it depends on the interpreter implementation.
    """

    signature: GenericFunctionSignature
    body: FunctionBody  # todo: GenericFunctionBody

    lexical_scope: Scope

    def __init__(self, lexical_scope: Scope | None, name: str = None, return_type: ImplementsType | Parameter | GenericParameter = Any):
        self.signature = GenericFunctionSignature(name, return_type)
        self.lexical_scope = lexical_scope
        self.body = FunctionBody(self)

    @property
    def name(self):
        return self.signature.name

    @name.setter
    def name(self, value: str):
        self.signature.name = value

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
    def variadic_positional_parameter(self, value: Parameter | GenericParameter | None):
        self.signature.variadic_positional_parameter = value

    @property
    def variadic_named_parameter(self):
        return self.signature.variadic_named_parameter

    @variadic_named_parameter.setter
    def variadic_named_parameter(self, value: Parameter | GenericParameter | None):
        self.signature.variadic_named_parameter = value

    @property
    def return_type(self):
        return self.signature.return_type

    @return_type.setter
    def return_type(self, value: ImplementsType):
        self.signature.return_type = value

    def construct(
            self,
            args: dict[Parameter | GenericParameter, ObjectProtocol | Parameter | GenericParameter],
            factory: Callable[[Scope], _T | Function] = None,
            generic_factory: Callable[[Scope], "_GenericT | GenericFunction"] = None
    ) -> _T | _GenericT:
        signature = self.signature.construct(args)

        if isinstance(signature, IConstructor):
            result = (generic_factory or GenericFunction)(self.lexical_scope)
        else:
            result = (factory or Function)(self.lexical_scope)

        result.signature = signature

        # result.body = resolve_body(self.body) if self.body else self.body todo

        return result

    def __repr__(self):
        return repr(self.signature) + " {}"


if __name__ == '__main__':
    from miniz.type_system import Type, Boolean

    generic = GenericFunction(None, "foo")

    T = Parameter("T", Type)
    X = GenericParameter("X", T)
    Y = GenericParameter("Y", X)
    Z = GenericParameter("Z", X)

    generic.positional_parameters.append(T)
    generic.positional_parameters.append(X)
    generic.positional_parameters.append(Y)
    generic.positional_parameters.append(Z)

    generic.return_type = Y

    print(generic)

    concrete = generic.construct({T: Type, X: Boolean})

    print(concrete)

    print(generic.construct({Y: Boolean.TrueInstance}))
