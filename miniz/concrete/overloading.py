import typing
from typing import Generic, TypeVar

from miniz.core import TypeProtocol
from miniz.interfaces.base import INamed, ScopeProtocol
from miniz.interfaces.function import IFunction
from miniz.ownership import Owned

if typing.TYPE_CHECKING:
    from miniz.type_system import TypeProtocol

_T = TypeVar("_T", bound=IFunction)


class OverloadGroupType(TypeProtocol):
    _group: "OverloadGroup"

    def __init__(self, group: "OverloadGroup"):
        self._group = group

    @property
    def group(self):
        return self._group

    def assignable_to(self, target: "TypeProtocol") -> bool:
        ...

    def assignable_from(self, source: "TypeProtocol") -> bool:
        ...


class OverloadGroup(Owned, INamed, Generic[_T]):
    overloads: list[_T]
    parent: "OverloadGroup | None"

    def __init__(self, name: str, parent: "OverloadGroup | None", *, owner=None):
        super().__init__(owner=owner)
        self.name = name
        self.parent = parent
        self.overloads = []

        self.runtime_type = OverloadGroupType(self)

    def get_match(self, args: list["TypeProtocol"], kwargs: list[tuple[str, "TypeProtocol"]], *, strict: bool = False, recursive: bool = False) -> list[_T]:
        from miniz.type_system import assignable_to, are_identical

        if recursive:
            overloads = self.get_match(args, kwargs, strict=strict, recursive=False)
            if not overloads:
                if self.parent is None:
                    return []
                return self.parent.get_match(args, kwargs, strict=strict, recursive=recursive)
            return overloads

        compare_type = assignable_to if not strict else are_identical

        overloads = []
        for overload in self.overloads:
            fits = True

            sig = overload.signature
            if len(args) > len(sig.positional_parameters) and sig.variadic_positional_parameter is None:
                continue
            if len(kwargs) > len(sig.named_parameters) and sig.variadic_named_parameter is None:
                continue

            for arg, param in zip(args, sig.positional_parameters):
                if not compare_type(arg, param.parameter_type):
                    fits = False
                    break
            if len(args) > len(sig.positional_parameters):
                for arg in args[len(sig.positional_parameters):]:
                    if not compare_type(arg, sig.variadic_positional_parameter.parameter_type):
                        fits = False
                        break
            elif len(args) < len(sig.positional_parameters):
                for param in sig.positional_parameters[len(args):]:
                    if not param.has_default_value:
                        fits = False
                        break
            if not fits:
                continue

            kw_params = {
                param.name: param for param in sig.named_parameters
            }
            for name, arg in kwargs:
                try:
                    param = kw_params[name]
                except KeyError:
                    if sig.variadic_named_parameter is None:
                        fits = False
                        break
                    param = sig.variadic_named_parameter
                if not compare_type(arg, param.parameter_type):
                    fits = False
                    break
            else:
                if len(kwargs) > len(sig.named_parameters):
                    for arg in args[len(sig.named_parameters):]:
                        if not compare_type(arg, sig.variadic_positional_parameter.parameter_type):
                            fits = False
                            break
                elif len(kwargs) < len(sig.named_parameters):
                    for param in sig.named_parameters[len(kwargs):]:
                        if not param.has_default_value:
                            fits = False
                            break

            if not fits:
                continue

            overloads.append(overload)

        return overloads
