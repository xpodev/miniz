from dataclasses import dataclass
from enum import Enum
from typing import Callable

from miniz.concrete.overloading import OverloadGroup
from miniz.generic import IGeneric
from miniz.interfaces.base import INamed
from miniz.interfaces.function import IFunction, IFunctionBody
from miniz.interfaces.signature import IParameter
from miniz.ownership import Owned
from miniz.core import TypeProtocol


class Binding(Enum):
    Static = "Static"
    Class = "Class"
    Instance = "Instance"
    Virtual = "Virtual"


class IDefinition:
    """
    Represents a definition object. A definition object holds actual object data. Modifying this object
    results in modifying the original object, as this object represents the original object.
    """

    def get_reference(self, **kwargs) -> "IReference":
        """
        :param kwargs: Additional keyword arguments to pass to the reference constructor.
        :return: a reference object which refers to this object.
        """
        raise NotImplementedError


class IReference:
    """
    Represents a reference to a definition object. Inheritors may add more information as they see fit.
    Modifying this object will not modify the original.
    """

    def get_definition(self) -> "IDefinition":
        """
        :return: The object definition which this object refers to.
        """


class IOOPMemberDefinition(Owned["IOOPDefinition"], IDefinition, INamed):
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

    @property
    def is_virtual_bound(self):
        return self.binding == Binding.Virtual

    def get_reference(self, **kwargs) -> "IReference":
        return IOOPMemberReference(self, **kwargs)


class IOOPMemberReference(Owned["IOOPReference"], IReference, INamed):
    _definition: IOOPMemberDefinition | IDefinition

    def __init__(self, origin: IOOPMemberDefinition | IDefinition, owner: "IOOPReference" = None):
        Owned.__init__(self, owner=owner or origin.owner)
        self._definition = origin

    @property
    def binding(self):
        return self._definition.binding

    @property
    def name(self):
        return self._definition.name

    @name.setter
    def name(self, value: str):
        ...

    def get_definition(self) -> "IDefinition":
        return self._definition


class IField(IOOPMemberDefinition):
    field_type: TypeProtocol


class IMethodBody(IFunctionBody):
    has_this: bool
    has_cls: bool
    has_context: bool
    this_parameter: IParameter | None
    cls_parameter: IParameter | None
    context_parameter: IParameter | None

    @property
    def method(self) -> "IMethod | None":
        return self.owner


class IMethod(IOOPMemberDefinition, IFunction):
    body: IMethodBody


class IProperty(IOOPMemberDefinition):
    property_type: TypeProtocol
    getter: IMethod | None
    setter: IMethod | None


class IOOPReference(IOOPMemberReference, TypeProtocol):
    _definition: "IOOPDefinition"

    def get_definition(self) -> "IOOPDefinition":
        return self._definition

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return self.get_definition().assignable_to(target)

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return self.get_definition().assignable_from(source)


class IOOPDefinition(IOOPMemberDefinition, IGeneric, TypeProtocol):
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
