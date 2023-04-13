from typing import TypeVar, Generic, Callable

from miniz.type_system import ObjectProtocol

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
