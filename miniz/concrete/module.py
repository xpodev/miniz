from typing import TypeVar

from miniz.concrete.function import Function
from miniz.core import ImplementsType
from miniz.generic.oop import ConstructedClass, ConstructedInterface, ConstructedTypeclass
from miniz.concrete.oop import Class, Interface, Typeclass
from miniz.interfaces.module import IModule, IModuleAPI, IGlobal
from miniz.interfaces.oop import IClass, IInterface, ITypeclass, IStructure
from miniz.ownership import Owned, Member
from miniz.type_system import ObjectProtocol
from utils import NotifyingList

_T = TypeVar("_T")


class GlobalValue(IGlobal, Owned["Module"]):
    def __init__(self, name: str, type: ImplementsType, default_value: ObjectProtocol | None = None):
        super().__init__()
        self.name = name
        self.type = type
        self.default_value = default_value


class ModuleAPI(IModuleAPI):
    ...


class Module(IModule):
    name: str | None

    _members: dict[str, Member]
    _member_list: list[Member]

    _functions: NotifyingList[Function]

    _classes: NotifyingList[IClass]
    _interfaces: NotifyingList[IInterface]
    _typeclasses: NotifyingList[ITypeclass]
    _structures: NotifyingList[IStructure]

    _types: NotifyingList[IClass, IInterface, ITypeclass, IStructure]

    _module_apis: NotifyingList["IModuleAPI"]
    _submodules: NotifyingList["Module"]

    _globals: NotifyingList[GlobalValue]

    _entry_point: Function | None

    def __init__(self, name: str | None = None):
        super().__init__()

        self.name = name

        self._members = {}
        self._member_list = []

        self.specifications = []

        self._functions = NotifyingList()
        self._classes = NotifyingList()
        self._interfaces = NotifyingList()
        self._typeclasses = NotifyingList()

        self._submodules = NotifyingList()

        self._globals = NotifyingList()

        self._entry_point = None

        def on_add_member(_, member: Member):
            if member.name and member.name not in self._members:
                self._members[member.name] = member
            self._member_list.append(member)
            member.owner = self

        def on_remove_member(ms, member: int | Member):
            if isinstance(member, int):
                member = ms[member]
            if member.name:
                del self._members[member.name]
            self._member_list.remove(member)
            member.owner = None

        self._globals.append += on_add_member

        self._globals.pop += on_remove_member
        self._globals.remove += on_remove_member

    @property
    def entry_point(self) -> Function:
        return self._entry_point

    @entry_point.setter
    def entry_point(self, value: Function):
        if value is None:
            if self._entry_point is None:
                return
            self._entry_point = None
        else:
            if type(value) is not Function:
                raise TypeError(f"Module entry point must be a valid function and not a subclass of it. got {type(value)}")
            if value.owner is not self:
                raise ValueError(f"Only a member function of a module may be set as its entry point")
            self._entry_point = value

    @property
    def has_entry_point(self):
        return self._entry_point is not None

    @property
    def types(self):
        return self._types

    @property
    def items(self):
        return [
            *self._classes,
            *self._functions,
            *self._typeclasses,
            *self._interfaces,
            *self._globals
        ]


class ModuleAPIImplementation:
    """
    Holds information on a single module-api implementation.

    This object holds a double mapping from items in the api to items in the implementation and vice versa.
    """

    implementation: Module
    specification: ModuleAPI

    implementation_to_specification_mapping: dict[Owned[Module], Owned[ModuleAPI]]
    specification_to_implementation_mapping: dict[Owned[ModuleAPI], Owned[Module]]

    def __init__(self, specification: ModuleAPI, implementation: Module):
        self.specification = specification
        self.implementation = implementation

    def add_item(self, specification: Owned[ModuleAPI], implementation: Owned[Module]):
        self.implementation_to_specification_mapping[implementation] = specification
        self.specification_to_implementation_mapping[specification] = implementation


def create_implementation(api: ModuleAPI, module: Module):
    ...
