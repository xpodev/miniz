from typing import Generic, TypeVar

from miniz.function import Function
from miniz.generic.oop import ConstructedClass, ConstructedInterface, ConstructedTypeclass
from miniz.oop import Class, Interface, Typeclass
from miniz.type_system import ObjectProtocol
from utils import NotifyingList

_T = TypeVar("_T")


class Member:
    name: str
    module: "Module"


class ObjectWrapper(Member, Generic[_T]):
    wrapped: _T

    def __init__(self, wrapped: _T, name: str | None = None, module: "Module" = None):
        if hasattr(wrapped, "name"):
            name = wrapped.name
        if name is None:
            raise ValueError(f"Module member must have a name")
        self.name = name
        self.wrapped = wrapped
        self.module = module


class GlobalValue(Member):
    name: str
    value: ObjectProtocol

    def __init__(self, name: str, value: ObjectProtocol):
        self.name = name
        self.value = value


class Module:
    name: str | None

    _members: dict[str, Member]
    _member_list: list[Member]

    _functions: NotifyingList[Function]
    _classes: NotifyingList[Class | ConstructedClass]
    _interfaces: NotifyingList[Interface, ConstructedInterface]
    _typeclasses: NotifyingList[Typeclass | ConstructedTypeclass]

    _globals: NotifyingList[GlobalValue]

    _entry_point: ObjectWrapper[Function] | None

    def __init__(self, name: str | None = None):
        self.name = name

        self._members = {}
        self._member_list = []

        self._functions = NotifyingList()
        self._classes = NotifyingList()
        self._interfaces = NotifyingList()
        self._typeclasses = NotifyingList()

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
        return self._entry_point.wrapped

    @entry_point.setter
    def entry_point(self, value: Function):
        if type(value) is not Function:
            raise TypeError(f"Module entry point must be a valid function and not a subclass of it. got {type(value)}")
        self._entry_point = ObjectWrapper(value, "{entrypoint}", self)
