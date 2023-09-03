from typing import TypeVar

from miniz.concrete.function import Function
from miniz.concrete.overloading import OverloadGroup
from miniz.core import TypeProtocol, ScopeProtocol
from miniz.template.oop import ConstructedClass, ConstructedInterface, ConstructedTypeclass
from miniz.concrete.oop import Class, Interface, Typeclass
from miniz.interfaces.base import INamed
from miniz.interfaces.function import IFunction
from miniz.interfaces.module import IModule, IModuleAPI, IGlobal
from miniz.interfaces.oop import IClass, IInterface, ITypeclass, IStructure
from miniz.ownership import Owned, Member
from miniz.type_system import ObjectProtocol
from utils import NotifyingList
from zs.zs2miniz.lib import Scope

_T = TypeVar("_T")
_U = TypeVar("_U")

_SENTINEL = object()


class GlobalValue(IGlobal, Owned["Module"]):
    def __init__(self, name: str, type: TypeProtocol, default_value: ObjectProtocol | None = None):
        super().__init__()
        self.name = name
        self.type = type
        self.default_value = default_value


class ModuleAPI(IModuleAPI):
    ...


class ModuleType(TypeProtocol, ScopeProtocol):
    _module: "Module"

    def __init__(self, module: "Module"):
        self._module = module

    @property
    def module(self):
        return self._module

    def get_name(self, name: str) -> ObjectProtocol:
        return self.module.get_name(name)

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return source is self

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return target is self


class Module(IModule):
    name: str | None

    _scope: Scope

    _functions: list[IFunction]

    _classes: list[IClass]
    _interfaces: list[IInterface]
    _typeclasses: list[ITypeclass]
    _structures: list[IStructure]

    _types: NotifyingList[IClass, IInterface, ITypeclass, IStructure]

    _module_apis: NotifyingList["IModuleAPI"]
    _submodules: NotifyingList["Module"]

    _globals: NotifyingList[GlobalValue]

    _entry_point: Function | None

    def __init__(self, name: str | None = None):
        super().__init__()

        self.name = name
        self.runtime_type = ModuleType(self)

        self._scope = Scope()

        self.specifications = []

        self._functions = NotifyingList()

        self._classes = []
        self._interfaces = []
        self._typeclasses = []
        self._structures = []

        self._types = NotifyingList()

        self._submodules = NotifyingList()

        self._globals = NotifyingList()

        self._entry_point = None

        def on_add_member(ms, member: Member):
            collection: list | None = None
            match member:
                case IFunction() as member:
                    if member.name:
                        group = self._scope.lookup_name(member.name, default=None)
                        if group is None:
                            self._scope.create_name(member.name, group := OverloadGroup(member.name, None, owner=self))
                        group.overloads.append(member)
                case IClass():
                    collection = self._classes
                case IInterface():
                    collection = self._interfaces
                case ITypeclass():
                    collection = self._typeclasses
                case IStructure():
                    collection = self._structures
                case Module():
                    collection = self._submodules
                case IModuleAPI():
                    collection = self._module_apis
            if collection is not None:
                collection.append(member)
            if isinstance(member, INamed) and not isinstance(member, IFunction):
                self._scope.create_name(member.name, member)
            member.owner = self

        def on_remove_member(ms, member: int | Member):
            if isinstance(member, int):
                member = ms[member]
            # if member.name:
            #     del self._members[member.name]
            # self._member_list.remove(member)
            member.owner = None

        self._globals.append += on_add_member

        self._globals.pop += on_remove_member
        self._globals.remove += on_remove_member

        self._types.append += on_add_member
        self._functions.append += on_add_member

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
    def functions(self):
        return self._functions

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
        # return self._scope.defined_items

    def get_name(self, name: str, *, default: _U = _SENTINEL) -> Owned["Module"] | _U:
        if default is _SENTINEL:
            return self._scope.lookup_name(name, recursive_lookup=False)
        return self._scope.lookup_name(name, recursive_lookup=False, default=default)


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
