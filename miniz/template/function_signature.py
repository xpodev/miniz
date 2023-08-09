from typing import Callable

from miniz.concrete.function_signature import FunctionSignature
from miniz.template.template_construction import IConstructor, recursive_resolve
from miniz.template.signature import SignatureTemplate, ParameterTemplate
from miniz.concrete.signature import Parameter
from miniz.interfaces.function import IFunctionSignature, IReturnParameter
from miniz.type_system import ImplementsType, Any, ObjectProtocol


class ReturnParameterTemplate(IReturnParameter):
    def __init__(self, signature: "FunctionSignatureTemplate", parameter_type: ImplementsType | Parameter | ParameterTemplate = None):
        super().__init__(owner=signature)
        self.parameter_type = parameter_type


class FunctionSignatureTemplate(SignatureTemplate, IFunctionSignature):
    def __init__(self, name: str = None, return_type: ImplementsType | Parameter = Any):
        super().__init__(name)
        IFunctionSignature.__init__(self)

        self.return_parameter = ReturnParameterTemplate(self, return_type)

    def construct(
            self,
            args: dict[Parameter | ParameterTemplate, ObjectProtocol],
            factory: Callable[[str], FunctionSignature] = None,
            generic_factory: Callable[[str], "FunctionSignatureTemplate"] = None
    ) -> "FunctionSignature | GenericFunctionSignature":
        result = super().construct(args, factory or FunctionSignature, generic_factory or FunctionSignatureTemplate)

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

    generic = FunctionSignatureTemplate("foo", T)

    value = ParameterTemplate("value", T)

    generic.positional_parameters.append(value)

    print(generic)

    concrete = generic.construct({T: Boolean})

    print(concrete)
