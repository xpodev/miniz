from miniz.interfaces.base import INamed
from miniz.interfaces.function import IFunction
from miniz.ownership import Owned
from miniz.type_system import ImplementsType, assignable_to


class OverloadGroup(Owned, INamed):
    overloads: list[IFunction]
    parent: "OverloadGroup | None"

    def get_match(self, args: list[ImplementsType], kwargs: list[tuple[str, ImplementsType]], *, recursive: bool = False) -> list[IFunction]:
        if recursive:
            overloads = self.get_match(args, kwargs, recursive=False)
            if not overloads:
                if self.parent is None:
                    return []
                return self.parent.get_match(args, kwargs, recursive=recursive)
            return overloads
        overloads = []
        for overload in self.overloads:
            sig = overload.signature
            if len(args) > len(sig.positional_parameters) and sig.variadic_positional_parameter is None:
                continue
            if len(kwargs) > len(sig.named_parameters) and sig.variadic_named_parameter is None:
                continue

            for arg, param in zip(args, sig.positional_parameters):
                if not assignable_to(arg, param.parameter_type):
                    continue
            if len(args) > len(sig.positional_parameters):
                for arg in args[len(sig.positional_parameters):]:
                    if not assignable_to(arg, sig.variadic_positional_parameter.parameter_type):
                        continue
            elif len(args) < len(sig.positional_parameters):
                for param in sig.positional_parameters[len(args):]:
                    if not param.has_default_value:
                        continue

            kw_params = {
                param.name: param for param in sig.named_parameters
            }
            for name, arg in kwargs:
                try:
                    param = kw_params[name]
                except KeyError:
                    if sig.variadic_named_parameter is None:
                        continue
                    param = sig.variadic_named_parameter
                if not assignable_to(arg, param.parameter_type):
                    continue

            overloads.append(overload)

        return overloads
