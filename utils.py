from enum import Enum
from typing import TypeVar, Generic, SupportsIndex, Mapping, Callable, Iterable

_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class Event:
    def __init__(self, fn):
        self.fn = fn
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name
        if not hasattr(owner, "_Event__event_mapping"):
            owner.__event_mapping = {}
        owner.__event_mapping[name] = {}

    def __get__(self, instance, owner):
        if instance is None:
            return self.fn
        ido = id(instance)
        if ido not in owner.__event_mapping[self.name]:
            owner.__event_mapping[self.name][ido] = EventInstance(instance, self.fn)
        return owner.__event_mapping[self.name][ido]


class EventInstance:
    def __init__(self, instance, fn):
        self.instance = instance
        self.fn = fn
        self.callbacks = []

    def __iadd__(self, other):
        assert callable(other)
        self.callbacks.append(other)
        return self

    def __isub__(self, other):
        assert callable(other)
        self.callbacks.remove(other)
        return self

    def __call__(self, *args, **kwargs):
        list(map(lambda f: f(self.instance, *args, **kwargs), self.callbacks))
        return self.fn(self.instance, *args, **kwargs)


def event(fn):
    return Event(fn)


class NotifyingList(list[_T], Generic[_T]):
    @event
    def append(self, __object: _T) -> None:
        return super().append(__object)

    @event
    def remove(self, __value: _T) -> None:
        return super().remove(__value)

    @event
    def pop(self, __index: SupportsIndex = ...) -> _T:
        return super().pop(__index)

    @event
    def __delitem__(self, key):
        return super().__delitem__(key)

    @event
    def __setitem__(self, key, value):
        return super().__setitem__(key, value)


class NotifyingDict(dict[_KT, _VT], Generic[_KT, _VT]):
    @event
    def update(self, __m: Mapping[_KT, _VT], **kwargs: _VT) -> None:
        return super().update(__m, **kwargs)

    @event
    def clear(self) -> None:
        return super().clear()

    @event
    def pop(self, __key: _KT) -> _VT:
        return super().pop(__key)

    @event
    def popitem(self) -> tuple[_KT, _VT]:
        return super().popitem()

    @event
    def __setitem__(self, key, value):
        return super().__setitem__(key, value)

    @event
    def __delitem__(self, key):
        return super().__delitem__(key)


class DependencyGraph(Generic[_T]):
    class CircularDependencyException(Exception):
        ...

    class Status(Enum):
        NotVisited = "NotVisited"
        Visiting = "Visiting"
        Visited = "Visited"

    @classmethod
    def from_list(cls, __items: Iterable[_T], dependency_finder: Callable[[_T], Iterable[_T]]) -> list[list[_T]]:
        statuses: dict[_T, DependencyGraph[_T].Status] = {}

        levels: dict[_T, int] = {}
        order: dict[int, list[_T]] = {}

        def recurse(item: _T, level: int, chain: list[_T]) -> int:
            try:
                status = statuses[item]
            except KeyError:
                statuses[item] = cls.Status.Visiting
            else:
                if statuses[item] == cls.Status.Visiting:
                    raise cls.CircularDependencyException(f"Circular dependency found: {' -> '.join(chain)}")
                if status == cls.Status.Visited:
                    return levels[item]
            items = dependency_finder(item)

            item_level = max((recurse(i, level + 1, [*chain, i]) for i in items), default=-1) + 1
            if item_level not in order:
                order[item_level] = []
            order[item_level].append(item)
            levels[item] = item_level
            statuses[item] = cls.Status.Visited

            return item_level

        for __item in __items:
            levels[__item] = recurse(__item, 0, [__item])

        return [order[i] for i in range(len(order))]


if __name__ == '__main__':
    objs = {
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["D"],
        # "D": ["B"],
        "D": []
    }

    res = DependencyGraph.from_list(objs, objs.__getitem__)
    print(res)
