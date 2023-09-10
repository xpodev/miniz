from miniz.core import ObjectProtocol, TypeProtocol
from miniz.interfaces.function import ILocal, IFunctionSignature
from miniz.interfaces.oop import IField
from miniz.interfaces.signature import IParameter
from miniz.type_system import assignable_to, Void


_SENTINEL = object()


class TypeStack:
    _stack: list[TypeProtocol]

    def __init__(self):
        self._stack = []

    def apply_signature(self, sig: IFunctionSignature):
        if len(self._stack) < len(sig.parameters):
            raise TypeError

        _cache = []

        for parameter in reversed(sig.parameters):
            tp = self.pop()
            _cache.append(tp)

            if not assignable_to(tp, parameter.parameter_type):
                break
        else:
            if sig.return_type is not Void:
                self.push_type(sig.return_type)

            return

        for tp in reversed(_cache):
            self.push_type(tp)

    def pop(self):
        return self._stack.pop()

    def pop_argument(self, value: IParameter):
        return self.pop_type(value.parameter_type)

    def pop_field(self, value: IField):
        return self.pop_type(value.field_type)

    def pop_local(self, value: ILocal):
        return self.pop_type(value.target_type)

    def pop_type(self, value: TypeProtocol):
        if not assignable_to(self.top(), value):
            raise TypeError
        return self.pop()

    def push_argument(self, value: IParameter):
        self.push_type(value.parameter_type)

    def push_field(self, value: IField):
        self.push_type(value.field_type)

    def push_local(self, value: ILocal):
        self.push_type(value.target_type)

    def push_object(self, value: ObjectProtocol):
        self.push_type(value.runtime_type)

    def push_type(self, value: TypeProtocol):
        self._stack.append(value)

    def top(self, default=_SENTINEL):
        try:
            return self._stack[-1]
        except IndexError:
            if default is _SENTINEL:
                raise
            return default
