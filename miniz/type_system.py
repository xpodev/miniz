"""
This module defines the core of the Z# type system. This may be used by both the generator and the interpreter.

Objects defined in this module should not be exposed to the Z# environment.
"""


class ObjectProtocol:
    runtime_type: "TypeProtocol"

    def is_instance_of(self, __type: "ImplementsType") -> bool:
        if isinstance(__type, TypeProtocol):
            return __type.is_instance(self)
        raise NotImplementedError(f"Currently, only types implemented on the Python level are supported.")


class TypeProtocol(ObjectProtocol):
    def is_instance(self, __object: ObjectProtocol) -> bool:
        return __object.runtime_type is self

    def assignable_to(self, target: "TypeProtocol") -> bool:
        raise NotImplementedError

    def assignable_from(self, source: "TypeProtocol") -> bool:
        raise NotImplementedError


def assignable_to(source: TypeProtocol, target: TypeProtocol) -> bool:
    return source.assignable_to(target) and target.assignable_from(source)


def assignable_from(target: TypeProtocol, source: TypeProtocol) -> bool:
    return assignable_to(source, target)


def is_type(__object) -> bool:
    if isinstance(__object, ImplementsType):
        return True


class _Type(TypeProtocol):
    def __init__(self):
        self.runtime_type = self

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return is_type(target.runtime_type)

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return is_type(source.runtime_type)

    def __repr__(self):
        return "type"


Type = _Type()
del _Type


class _TypeBase(TypeProtocol):
    def __init__(self):
        self.runtime_type = Type

    def assignable_to(self, target: "TypeProtocol") -> bool:
        raise NotImplementedError

    def assignable_from(self, source: "TypeProtocol") -> bool:
        raise NotImplementedError


class _Void(_TypeBase):
    def assignable_to(self, target: "TypeProtocol") -> bool:
        return False

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return False

    def __repr__(self):
        return "void"


Void = _Void()
del _Void


class _Unit(_TypeBase):
    class _Unit(ObjectProtocol):
        def __init__(self, runtime_type: "_Unit"):
            self.runtime_type = runtime_type

        def __repr__(self):
            return "()"

    def __init__(self):
        super().__init__()

        self.UnitInstance = self._Unit(self)

        del _Unit._Unit

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return target is self

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return source is self

    def __repr__(self):
        return "unit"


Unit = _Unit()
del _Unit


class _Boolean(_TypeBase):
    class _Boolean(ObjectProtocol):
        def __init__(self, value: bool, runtime_type: "_Boolean"):
            self.value = value
            self.runtime_type = runtime_type

        def __repr__(self):
            return "true" if self.value else "false"

    def __init__(self):
        super().__init__()

        self.TrueInstance = self._Boolean(True, self)
        self.FalseInstance = self._Boolean(False, self)

        del _Boolean._Boolean

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return target.assignable_from(self)

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return source is self

    def __repr__(self):
        return "bool"


Boolean = _Boolean()
del _Boolean


class _Any(_TypeBase):
    class _Undefined(ObjectProtocol):
        def __init__(self, runtime_type: "_Any"):
            self.runtime_type = runtime_type

        def __repr__(self):
            return "undefined"

    def __init__(self):
        super().__init__()

        self.UndefinedInstance = self._Undefined(self)

        del _Any._Undefined

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return target is Any

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return True

    def __repr__(self):
        return "any"


Any = _Any()
del _Any


class Nullable(TypeProtocol):
    def __init__(self, type: TypeProtocol):
        self.type = type

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return isinstance(target, Nullable) and target.type.assignable_to(self.type)

    def assignable_from(self, source: "TypeProtocol") -> bool:
        if source is Null:
            return True
        return self.type.assignable_from(source)

    def __repr__(self):
        return repr(self.type) + '?'


class _Null(_TypeBase):
    class _Null(ObjectProtocol):
        def __init__(self, runtime_type: "_Null"):
            self.runtime_type = runtime_type

        def __repr__(self):
            return "null"

    def __init__(self):
        super().__init__()

        self.NullInstance = self._Null(self)

        del _Null._Null

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return isinstance(target, Nullable)

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return source is _Null

    def __repr__(self):
        return "nulltype"


Null = _Null()
del _Null


del _TypeBase


ImplementsType = TypeProtocol


if __name__ == '__main__':
    print(Type)
    print(Void)
    print(Unit)
    print(Unit.UnitInstance)
    print(Boolean)
    print(Boolean.TrueInstance)
    print(Boolean.FalseInstance)
    print(Any)
    print(Any.UndefinedInstance)
    print(Null)
    print(Null.NullInstance)

    print(Nullable(Boolean))
    print("bool? <- bool ::", assignable_to(Boolean, Nullable(Boolean)))
    print("bool <- bool? ::", assignable_from(Boolean, Nullable(Boolean)))

    print(Type is Type.runtime_type is Void.runtime_type is Unit.runtime_type is Boolean.runtime_type is Any.runtime_type is Null.runtime_type)
