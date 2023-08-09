from typing import TypeVar, Generic, Callable

from miniz.core import ObjectProtocol
from miniz.interfaces.signature import IParameter

_T = TypeVar("_T")
_U = TypeVar("_U")


def recursive_resolve(args: dict[_T, ObjectProtocol | _T], start: _T) -> ObjectProtocol | _T:
    try:
        step = args[start]
    except KeyError:
        return start
    else:
        if step is start:
            raise ValueError
        return recursive_resolve(args, step)


class IConstructor(Generic[_T]):
    def construct(
            self,
            args: dict[_U, ObjectProtocol | _U],
            factory: Callable[[], _T] = None,
            generic_factory: Callable[[], "IConstructor[_T]"] = None
    ) -> "_T | IConstructor[_T]":
        ...


class IConstructed(Generic[_T]):
    def __init__(self, constructor: IConstructor[_T], arguments: dict[IParameter, ObjectProtocol | IParameter]):
        self._constructor = constructor
        self._constructor_arguments = arguments

    @property
    def constructor(self) -> IConstructor[_T]:
        return self._constructor

    @property
    def constructor_arguments(self) -> dict[IParameter, ObjectProtocol | IParameter]:
        return self._constructor_arguments
