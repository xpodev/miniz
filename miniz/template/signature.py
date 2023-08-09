from functools import partial
from typing import Callable, TypeVar, TypeAlias

from miniz.template.template_construction import IConstructor, recursive_resolve
from miniz.concrete.signature import Signature, Parameter
from miniz.interfaces.signature import ISignature, IParameter
from miniz.core import ObjectProtocol, ImplementsType
from miniz.ownership import Owned
from utils import NotifyingList, DependencyGraph

_T = TypeVar("_T")
_GenericT = TypeVar("_GenericT")
GenericArguments: TypeAlias = dict["Parameter | GenericParameter", "Parameter | GenericParameter | ObjectProtocol"]


_SENTINEL = Parameter('_')


def get_parameter_dependencies(args: GenericArguments, parameter: "Parameter | GenericParameter") -> list["Parameter | GenericParameter"]:
    if isinstance(parameter, Parameter):
        return []

    parameter_type = parameter.parameter_type
    if parameter in args and parameter_type in args:
        ...  # validate
    elif parameter in args:
        return []
    elif parameter_type in args:
        if not isinstance(parameter, GenericParameter):
            raise TypeError
        return [parameter_type]
    else:
        if not isinstance(parameter_type, ImplementsType):
            return [parameter_type]
    return []


class GenericParameter(IConstructor[Parameter], IParameter, Owned["GenericSignature"]):
    default_value: ObjectProtocol | None
    parameter_type: ImplementsType | IParameter

    def __init__(self, name: str, type: "ImplementsType | GenericParameter | Parameter" = None, default_value: ObjectProtocol = None):
        super().__init__()
        Owned.__init__(self)
        self.name = name
        self.parameter_type = type
        self.default_value = default_value

    @property
    def index(self):
        if self.owner is None:
            raise ValueError(f"Parameter currently doesn't have an index")
        return self.owner.parameters.index(self)

    @property
    def is_positional(self):
        return self in self.owner.positional_parameters

    @property
    def is_named(self):
        return self in self.owner.named_parameters

    @property
    def is_variadic_positional(self):
        return self.owner.variadic_positional_parameter is self

    @property
    def is_variadic_named(self):
        return self.owner.variadic_named_parameter is self

    def construct(self, args: dict["IParameter", "ObjectProtocol | IParameter"], factory=None, generic_factory=None) -> "IParameter":
        # if self.type is an actual type, skip infer and validation
        # if both self and self.type are in args, make sure they don't collide
        # if only self is in args, infer self.type and add it to args
        # if only self.type in args, construct normally
        parameter_type = recursive_resolve(args, self.parameter_type)
        default_value = self.default_value  # todo: generic eval default value
        if isinstance(parameter_type, (GenericParameter, Parameter)):
            result = (generic_factory or GenericParameter)(self.name, parameter_type, default_value)
        else:
            result = (factory or Parameter)(self.name, parameter_type, default_value)  # todo: generic eval default value
        return result

    def __repr__(self):
        return f"{self.name}: {self.parameter_type.name if isinstance(self.parameter_type, (GenericParameter, Parameter)) else self.parameter_type}" + (f" = {self.default_value}" if self.default_value is not None else "")


class GenericSignature(ISignature, IConstructor[Signature]):
    name: str | None

    _parameters: dict[str, GenericParameter | Parameter]

    _positional_parameters: NotifyingList[GenericParameter | Parameter]
    _named_parameters: NotifyingList[GenericParameter | Parameter]

    _variadic_positional_parameter: GenericParameter | Parameter | None
    _variadic_named_parameter: GenericParameter | Parameter | None

    def __init__(self, name: str = None):
        ISignature.__init__(self)
        self.name = name

        self._parameters = {}

        self._positional_parameters = NotifyingList()
        self._named_parameters = NotifyingList()

        def on_new_parameter(_, parameter: GenericParameter):
            if parameter.name in self._parameters:
                raise ValueError(f"Parameter \'{parameter.name}\' already exists on {self}")
            self._parameters[parameter.name] = parameter
            parameter.owner = self

        def on_remove_parameter(ps, parameter: int | GenericParameter):
            if isinstance(parameter, int):
                parameter = ps[parameter]
            assert isinstance(parameter, (Parameter, GenericParameter))
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
    def parameters(self) -> list[Parameter | GenericParameter]:
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
    def variadic_positional_parameter(self, value: GenericParameter | Parameter | None):
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
    def variadic_named_parameter(self, value: GenericParameter | Parameter | None):
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

    def _get_build_order(self, args: GenericArguments):
        all_parameters = list(filter(bool, [*self.positional_parameters, *self.named_parameters, self.variadic_positional_parameter, self.variadic_named_parameter]))

        return DependencyGraph.from_list(all_parameters, partial(get_parameter_dependencies, args))

    def construct(
            self,
            args: dict[Parameter | GenericParameter, ObjectProtocol | Parameter | GenericParameter],
            factory: Callable[[str], _T | Signature] = None,
            generic_factory: Callable[[str], "_GenericT | GenericSignature"] = None
    ) -> _T | _GenericT:
        constructed: dict[Parameter | GenericParameter, Parameter | GenericParameter] = {}

        build_order = self._get_build_order(args)

        def recursive_infer(p: GenericParameter):
            if p in args and p.parameter_type not in args:
                args[p.parameter_type] = args[p].runtime_type
                if isinstance(p.parameter_type, GenericParameter):
                    recursive_infer(p.parameter_type)

        for parameter in args.copy():
            if isinstance(parameter, GenericParameter):
                recursive_infer(parameter)

        for parameters in build_order:
            for parameter in parameters:
                if isinstance(parameter, GenericParameter):
                    if parameter not in args:
                        constructed[parameter] = args[parameter] = parameter.construct(args)

        positional_parameters = [constructed[parameter] for parameter in self.positional_parameters if parameter in constructed]
        named_parameters = [constructed[parameter] for parameter in self.named_parameters if parameter in constructed]

        variadic_positional_parameter = constructed.get(self.variadic_positional_parameter, None)
        variadic_named_parameter = constructed.get(self.variadic_named_parameter, None)

        if any(isinstance(p, IConstructor) for p in [*positional_parameters, *named_parameters, variadic_positional_parameter, variadic_named_parameter]):
            result = (generic_factory or GenericSignature)(self.name)
        else:
            result = (factory or Signature)(self.name)

        for parameter in positional_parameters:
            if parameter not in args:
                result.positional_parameters.append(parameter)
        for parameter in named_parameters:
            if parameter not in args:
                result.named_parameters.append(parameter)

        if variadic_positional_parameter not in args:
            result.variadic_positional_parameter = variadic_positional_parameter
        if variadic_named_parameter not in args:
            result.variadic_named_parameter = variadic_named_parameter

        return result

    def remove_parameter(self, parameter: Parameter | GenericParameter):
        if parameter.owner is not self:
            raise ValueError(f"{self} does not own {parameter}")
        index = parameter.index
        if index < len(self.positional_parameters):
            self.positional_parameters.remove(parameter)
        elif index < len(self.positional_parameters) + len(self.named_parameters):
            self.named_parameters.remove(parameter)
        elif parameter is self.variadic_positional_parameter:
            self.variadic_positional_parameter = None
        elif parameter is self.variadic_named_parameter:
            self.variadic_named_parameter = None
        else:
            raise ValueError(f"Unknown parameter location \'{parameter}\'")

    def __repr__(self):
        args = ", ".join(map(repr, self.positional_parameters))
        if self._named_parameters:
            args += (", " if args else "") + "{" + ", ".join(map(repr, self.named_parameters)) + "}"

        if self.variadic_positional_parameter:
            args += (", *" if args else '*') + repr(self.variadic_positional_parameter)
        if self.variadic_named_parameter:
            args += (", **" if args else "**") + repr(self.variadic_named_parameter)

        return f"{self.name or ''}({args})"


if __name__ == '__main__':
    from miniz.type_system import Type, Boolean

    # generic = GenericSignature("foo")
    #
    # T = Parameter("T", Type)
    # X = GenericParameter("X", T)
    # Y = GenericParameter("Y", X)
    # Z = GenericParameter("Z", X)
    #
    # generic.positional_parameters.append(T)
    # generic.positional_parameters.append(X)
    # generic.positional_parameters.append(Y)
    # generic.positional_parameters.append(Z)
    #
    # # print(generic)
    #
    # concrete = generic.construct({T: Type, X: Boolean})
    #
    # # print(generic.construct({Y: Boolean}))
    # # print(concrete)
    #
    generic = GenericSignature("bar")

    A, B, C, D, E, F = [Parameter("A"), *(GenericParameter(letter) for letter in "BCDEF")]
    A.parameter_type = Type
    B.parameter_type = A
    C.parameter_type = B
    D.parameter_type = C
    E.parameter_type = D
    F.parameter_type = E

    for p in [A, B, C, D, E, F]:
        generic.named_parameters.append(p)

    print(generic)

    print(generic.construct({E: Boolean}))
