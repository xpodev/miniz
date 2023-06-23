from miniz.interfaces.base import INamed
from miniz.ownership import Owned
from miniz.core import ImplementsType


class IParameter(Owned["ISignature"], INamed):
    index: int  # index of the parameter, including all types of parameters
    local_index: int  # index of positional or named parameter in its respective list
    parameter_type: ImplementsType
    has_default_value: bool

    @property
    def is_positional(self):
        return self in self.owner.positional_parameters

    @property
    def is_named(self):
        return self in self.owner.named_parameters

    @property
    def is_variadic(self):
        return self.is_variadic_positional or self.is_variadic_named

    @property
    def is_variadic_positional(self):
        return self.owner.variadic_positional_parameter is self

    @property
    def is_variadic_named(self):
        return self.owner.variadic_named_parameter is self


class ISignature(INamed):
    positional_parameters: list[IParameter]
    named_parameters: list[IParameter]
    variadic_positional_parameter: IParameter | None
    variadic_named_parameter: IParameter | None

    @property
    def parameters(self) -> list[IParameter]:
        result = [*self.positional_parameters, *self.named_parameters]
        if self.variadic_positional_parameter:
            result.append(self.variadic_positional_parameter)
        if self.variadic_named_parameter:
            result.append(self.variadic_named_parameter)
        return result
