from typing import Generic, TypeVar

from miniz.core import TypeProtocol, ObjectProtocol
from miniz.interfaces.signature import IParameter
from miniz.ownership import Owned
from utils import NotifyingList


_T = TypeVar("_T", bound="IGeneric")


class IGeneric:
    generic_signature: "GenericSignature | None"

    @property
    def is_generic(self):
        return self.generic_signature is not None

    @property
    def has_generic_parameters(self):
        return self.is_generic and self.generic_parameters

    @property
    def generic_parameters(self):
        return self.generic_signature.positional_parameters

    def make_generic(self):
        if self.is_generic:
            raise TypeError
        self.generic_signature = GenericSignature()

    def instantiate_generic(self, args: list[TypeProtocol]):
        if len(args) != len(self.generic_parameters):
            raise ValueError(f"Expected {len(self.generic_parameters)} types, got only {len(args)}")

        for arg in args:
            if not isinstance(arg, TypeProtocol):
                raise TypeError(f"Generic arguments must be types")  # todo: constraints?

        return GenericInstance(self, dict(zip(self.generic_parameters, args)))


class GenericInstance(ObjectProtocol, Generic[_T]):
    _origin: _T

    def __init__(self, origin: _T, arguments: dict["GenericParameter", TypeProtocol]):
        self._origin = origin
        self._instantiation_arguments = arguments

    @property
    def origin(self) -> _T:
        return self._origin

    @property
    def generic_arguments(self) -> dict["GenericParameter", TypeProtocol]:
        return self._instantiation_arguments


class GenericParameterType(TypeProtocol):
    definition: "GenericParameter"

    def __init__(self, definition: "GenericParameter"):
        self.definition = definition

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return target is self.definition

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return source is self.definition


class GenericParameter(IParameter, TypeProtocol):
    def __init__(self, name: str):
        super().__init__()

        self.name = name
        self.runtime_type = GenericParameterType(self)

    @property
    def parameter_type(self):
        from miniz.type_system import Type

        return Type

    def assignable_from(self, source: TypeProtocol) -> bool:
        return source is self

    def assignable_to(self, target: TypeProtocol) -> bool:
        return target is self

    def __str__(self):
        return f"Generic<{self.name}>"


class GenericSignature(Owned["IFunction"]):
    _positional_parameters: NotifyingList[GenericParameter]

    def __init__(self):
        super().__init__()

        self._positional_parameters = NotifyingList()

        def on_new_parameter(_, parameter: GenericParameter):
            if any(p.name == parameter.name for p in self._positional_parameters):
                raise ValueError(f"Parameter \'{parameter.name}\' already exists on {self}")
            parameter.owner = self

        def on_remove_parameter(ps, parameter: int | GenericParameter):
            if isinstance(parameter, int):
                parameter = ps[parameter]
            assert isinstance(parameter, GenericParameter)
            parameter.owner = None

        self._positional_parameters.append += on_new_parameter

        self._positional_parameters.pop += on_remove_parameter
        self._positional_parameters.remove += on_remove_parameter

        self.__on_new_parameter = on_new_parameter
        self.__on_remove_parameter = on_remove_parameter

    @property
    def parameters(self):
        return self.positional_parameters

    @property
    def positional_parameters(self):
        return self._positional_parameters
