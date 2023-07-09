from typing import TypeVar, Generic, Any

from miniz.interfaces.base import IMiniZObject

_T = TypeVar("_T", bound="Owned")


class Member(Generic[_T]):
    as_free_object: _T
    owner: Any

    def __init__(self, owner: Any, owned: _T):
        self.owner = owner
        self.as_free_object = owned


class Owned(IMiniZObject, Generic[_T]):
    """
    Base class for all objects that may be owned by another object.

    Deriving classes should retype the `as_member` field as `Member[{class}]` for better typing.
    """
    as_member: Member["Owned[_T]"] | None

    def __init__(self, *, owner: _T = None):
        self.as_member = Member(owner, self) if owner is not None else None

    @property
    def is_member(self):
        return self.as_member is not None

    @property
    def owner(self) -> _T | None:
        return self.as_member.owner if self.as_member is not None else None

    @owner.setter
    def owner(self, value: _T | None):
        self.as_member = Member(value, self) if value is not None else None

    def is_direct_member_of(self, owner: Any) -> bool:
        if not self.is_member:
            return False
        return self.as_member.owner is owner

    def is_indirect_member_of(self, owner: Any):
        if not self.is_member:
            return False
        if self.is_direct_member_of(owner):
            return True
        if isinstance(self.as_member.owner, Owned):
            return self.as_member.owner.is_indirect_member_of(owner)
