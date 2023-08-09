from miniz.interfaces.signature import ISignature, IParameter
from miniz.core import TypeProtocol, ObjectProtocol
from utils import NotifyingList


class Parameter(IParameter):
    parameter_type: TypeProtocol
    default_value: ObjectProtocol | None

    def __init__(self, name: str, type: TypeProtocol = None, default_value: ObjectProtocol = None):
        super().__init__()
        self.name = name
        self.parameter_type = type
        self.default_value = default_value

    @property
    def index(self):
        if self.owner is None:
            raise ValueError(f"Parameter currently doesn't have an index")
        return self.owner.parameters.index(self)

    @property
    def has_default_value(self):
        return self.default_value is not None

    def __repr__(self):
        return f"{self.name}: {self.parameter_type}" + (f" = {self.default_value}" if self.default_value is not None else "")


class Signature(ISignature):
    _parameters: dict[str, Parameter]

    _positional_parameters: NotifyingList[Parameter]
    _named_parameters: NotifyingList[Parameter]

    _variadic_positional_parameter: Parameter | None
    _variadic_named_parameter: Parameter | None

    def __init__(self, name: str = None):
        self.name = name

        self._parameters = {}

        self._positional_parameters = NotifyingList()
        self._named_parameters = NotifyingList()

        def on_new_parameter(_, parameter: Parameter):
            if parameter.name in self._parameters:
                raise ValueError(f"Parameter \'{parameter.name}\' already exists on {self}")
            self._parameters[parameter.name] = parameter
            parameter.owner = self

        def on_remove_parameter(ps, parameter: int | Parameter):
            if isinstance(parameter, int):
                parameter = ps[parameter]
            assert isinstance(parameter, Parameter)
            del self._parameters[parameter.name]
            parameter.owner = None

        self._positional_parameters.append += on_new_parameter
        self._named_parameters.append += on_new_parameter

        self._positional_parameters.pop += on_remove_parameter
        self._named_parameters.pop += on_remove_parameter
        self._positional_parameters.remove += on_remove_parameter
        self._named_parameters.remove += on_remove_parameter

        self.__on_new_parameter = on_new_parameter
        self.__on_remove_parameter = on_remove_parameter

        self._variadic_positional_parameter = self._variadic_named_parameter = None

    @property
    def parameters(self) -> list[Parameter]:
        result = [*self.positional_parameters, *self.named_parameters]
        if self.variadic_positional_parameter:
            result.append(self.variadic_positional_parameter)
        if self.variadic_named_parameter:
            result.append(self.variadic_named_parameter)
        return result

    @property
    def positional_parameters(self):
        return self._positional_parameters

    @property
    def named_parameters(self):
        return self._named_parameters

    @property
    def variadic_positional_parameter(self):
        return self._variadic_positional_parameter

    @variadic_positional_parameter.setter
    def variadic_positional_parameter(self, value: Parameter | None):
        if value is None and self.variadic_positional_parameter is None:
            return
        if value is None:
            self.__on_remove_parameter(None, self.variadic_positional_parameter)
            self._variadic_positional_parameter = None
        else:
            if self.variadic_positional_parameter is not None:
                self.variadic_positional_parameter = None
            self.__on_new_parameter(None, value)
            self._variadic_positional_parameter = value

    @property
    def variadic_named_parameter(self):
        return self._variadic_named_parameter

    @variadic_named_parameter.setter
    def variadic_named_parameter(self, value: Parameter | None):
        if value is None and self.variadic_named_parameter is None:
            return
        if value is None:
            self.__on_remove_parameter(None, self.variadic_named_parameter)
            self._variadic_named_parameter = None
        else:
            if self.variadic_named_parameter is not None:
                self.variadic_named_parameter = None
            self.__on_new_parameter(None, value)
            self._variadic_named_parameter = value

    def __repr__(self):
        args = ", ".join(map(repr, self._positional_parameters))
        if self._named_parameters:
            args += (", " if args else "") + "{" + ", ".join(map(repr, self._named_parameters)) + "}"

        if self.variadic_positional_parameter:
            args += (", *" if args else '*') + repr(self.variadic_positional_parameter)
        if self.variadic_named_parameter:
            args += (", **" if args else "**") + repr(self.variadic_named_parameter)

        return f"{self.name or ''}({args})"
