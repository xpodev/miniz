from dataclasses import dataclass
from enum import Enum
from typing import Callable

from miniz.concrete.overloading import OverloadGroup
from miniz.interfaces.base import INamed
from miniz.interfaces.function import IFunction
from miniz.ownership import Owned
from miniz.core import ImplementsType, TypeProtocol


class Binding(Enum):
    Static = "Static"
    Class = "Class"
    Instance = "Instance"


class IOOPMember(Owned["IClass | IInterface | ITypeclass | IStructure"], INamed):
    binding: Binding

    @property
    def is_instance_bound(self):
        return self.binding == Binding.Instance

    @property
    def is_class_bound(self):
        return self.binding == Binding.Class

    @property
    def is_static_bound(self):
        return self.binding == Binding.Static


class IField(IOOPMember):
    field_type: ImplementsType


class IMethod(IOOPMember, IFunction):
    ...


class IProperty(IOOPMember):
    property_type: ImplementsType
    getter: IMethod | None
    setter: IMethod | None


class IOOPDefinition(IOOPMember, TypeProtocol):
    fields: list[IField]
    methods: list[IMethod]
    properties: list[IProperty]
    nested_definitions: list["IOOPDefinition"]

    runtime_type_constructor: Callable[["IOOPDefinition"], TypeProtocol]

    binding = Binding.Static

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return super().assignable_to(target)

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return super().assignable_from(source)


class IClass(IOOPDefinition):
    base: "IClass | None"
    specifications: list["OOPImplementable"]
    constructor: OverloadGroup[IMethod]

    @property
    def constructors(self):
        return self.constructor.overloads


@dataclass(slots=True)
class ImplementationInfo:
    """
    Holds information on a single implementation.
    """

    specification: "OOPImplementable"
    """
    The object that defines the API which should be implemented.
    """

    implementation: IClass
    """
    The class that contains the actual implementation. Might but doesn't have to be the implemented type.
    """

    implemented_type: IClass
    """
    The class that implements the specification. This class doesn't have to contain the actual implementation.
    """


class OOPImplementable(IOOPDefinition):
    implementations: list[ImplementationInfo]
    implementations_mapping: dict[IClass, ImplementationInfo]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.implementations = []
        self.implementations_mapping = {}

    def add_implementation(self, implemented_type: IClass, implementation: IClass | None):
        info = ImplementationInfo(self, implementation or implemented_type, implemented_type)
        self.implementations.append(info)
        self.implementations_mapping[implemented_type] = info

    def get_implementation(self, implemented_type: IClass) -> ImplementationInfo | None:
        try:
            return self.implementations_mapping[implemented_type]
        except KeyError:
            return None

    def is_implemented(self, implemented_type: IClass):
        return implemented_type in self.implementations_mapping


class IInterface(OOPImplementable):
    bases: list["IInterface"]


class ITypeclass(OOPImplementable):
    class TypeclassTypeVariable:
        typeclass: "ITypeclass"

        def __init__(self, typeclass: "ITypeclass"):
            self.typeclass = typeclass

    bases: list["ITypeclass"]
    implemented_type_variable: TypeclassTypeVariable

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bases = []
        self.implemented_type_variable = self.TypeclassTypeVariable(self)


class IStructure(OOPImplementable):
    bases: list["IStructure"]
