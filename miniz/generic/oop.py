import typing

from miniz.core import TypeProtocol, ObjectProtocol
from miniz.generic import GenericInstance
from miniz.interfaces.base import ScopeProtocol
from miniz.interfaces.oop import IClass, IOOPMemberDefinition, IOOPReference
from miniz.interfaces.signature import IParameter

if typing.TYPE_CHECKING:
    from miniz.concrete.oop import Class


class GenericClassInstanceType(TypeProtocol, ScopeProtocol):
    _class: "GenericClassInstance"

    def __init__(self, origin: "GenericClassInstance"):
        self._class = origin

    def assignable_to(self, target: "TypeProtocol") -> bool:
        ...

    def assignable_from(self, source: "TypeProtocol") -> bool:
        ...

    def get_name(self, name: str) -> ObjectProtocol:
        return self._class.get_name(name)


class GenericClassInstanceMemberReference:
    owner: "GenericClassInstance"

    def __init__(self, original: IOOPMemberDefinition, owner: "GenericClassInstance"):
        super().__init__()
        self.owner = owner
        self.original = original

    @property
    def runtime_type(self):
        return self.original.runtime_type


class GenericClassInstance(GenericInstance[IClass], ScopeProtocol, IOOPReference):
    origin: "Class"

    def __init__(self, origin: IClass, args: dict[IParameter, TypeProtocol]):
        super().__init__(origin, args)
        IOOPReference.__init__(self, origin)

        self.runtime_type = GenericClassInstanceType(self)

    def assignable_from(self, source: "TypeProtocol") -> bool:
        ...

    def assignable_to(self, target: "TypeProtocol") -> bool:
        ...

    def get_name(self, name: str):
        result = self.origin.get_name(name)
        return result.get_reference(owner=self)
