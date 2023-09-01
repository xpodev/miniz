from typing import TypeVar

from miniz.core import TypeProtocol
from miniz.ownership import Owned
from miniz.vm.instruction import Instruction


_T = TypeVar("_T", bound="IExecutable")


class ITarget(Owned[_T]):
    """
    Represents a local memory location, owned by a certain scope which is itself represented by the executable
    scope. Does not represent a reference to a location, but always a local location (function local, CT local, etc..)
    """

    target_type: TypeProtocol

    @property
    def index(self):
        return self.owner.locals.index(self)


class IExecutable:
    instructions: list[Instruction]
    locals: list[ITarget]
