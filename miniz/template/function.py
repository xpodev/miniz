from typing import Callable, TypeVar

from miniz.concrete.function import Function, FunctionBody, Local
from miniz.template.template_construction import IConstructor
from miniz.template.function_signature import FunctionSignatureTemplate
from miniz.template.signature import ParameterTemplate
from miniz.concrete.signature import Parameter
from miniz.interfaces.function import IFunction
from miniz.type_system import ImplementsType, Any, ObjectProtocol
from utils import NotifyingList

_T = TypeVar("_T")
_GenericT = TypeVar("_GenericT")


class FunctionTemplate(IFunction, IConstructor[Function]):
    """
    Represents a generic Z# function. This object should not be exposed to the Z# environment.

    Currently, the function's body may be represented by any object, and it depends on the interpreter implementation.
    """

    signature: FunctionSignatureTemplate
    body: FunctionBody  # todo: GenericFunctionBody

    _locals: NotifyingList[Local]

    def __init__(self, name: str = None, return_type: ImplementsType | Parameter | ParameterTemplate = Any):
        super().__init__()

        self.signature = FunctionSignatureTemplate(name, return_type)

        self.body = FunctionBody(self)
        self._locals = NotifyingList()

    @property
    def name(self):
        return self.signature.name

    @name.setter
    def name(self, value: str):
        self.signature.name = value

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
    def variadic_positional_parameter(self, value: Parameter | ParameterTemplate | None):
        self.signature.variadic_positional_parameter = value

    @property
    def variadic_named_parameter(self):
        return self.signature.variadic_named_parameter

    @variadic_named_parameter.setter
    def variadic_named_parameter(self, value: Parameter | ParameterTemplate | None):
        self.signature.variadic_named_parameter = value

    @property
    def return_type(self):
        return self.signature.return_type

    @return_type.setter
    def return_type(self, value: ImplementsType):
        self.signature.return_type = value

    def construct(
            self,
            args: dict[Parameter | ParameterTemplate, ObjectProtocol | Parameter | ParameterTemplate],
            factory: Callable[[], _T | Function] = None,
            generic_factory: Callable[[], "_GenericT | GenericFunction"] = None
    ) -> _T | _GenericT:
        signature = self.signature.construct(args)

        if isinstance(signature, IConstructor):
            result = (generic_factory or FunctionTemplate)()
        else:
            result = (factory or Function)()

        result.signature = signature

        # result.body = resolve_body(self.body) if self.body else self.body todo

        return result

    def __repr__(self):
        return repr(self.signature) + " {}"


if __name__ == '__main__':
    from miniz.type_system import Type, Boolean

    generic = FunctionTemplate(None, "foo")

    T = Parameter("T", Type)
    X = ParameterTemplate("X", T)
    Y = ParameterTemplate("Y", X)
    Z = ParameterTemplate("Z", X)

    generic.positional_parameters.append(T)
    generic.positional_parameters.append(X)
    generic.positional_parameters.append(Y)
    generic.positional_parameters.append(Z)

    generic.return_type = Y

    print(generic)

    concrete = generic.construct({T: Type, X: Boolean})

    print(concrete)

    print(generic.construct({Y: Boolean.TrueInstance}))
