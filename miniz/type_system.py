"""
This module defines the core of the Z# type system. This may be used by both the generator and the interpreter.

Objects defined in this module should not be exposed to the Z# environment.
"""

from miniz.concrete.oop import Class, Field, Access, Method
from miniz.core import TypeProtocol, ImplementsType, ObjectProtocol
from miniz.interfaces.oop import Binding
from miniz.vm import instructions as vm


def assignable_to(source: TypeProtocol, target: TypeProtocol) -> bool:
    return source.assignable_to(target) and target.assignable_from(source)


def assignable_from(target: TypeProtocol, source: TypeProtocol) -> bool:
    return assignable_to(source, target)


def is_type(__object) -> bool:
    if isinstance(__object, ImplementsType):
        return True


class _Type(Class):
    def __init__(self):
        super().__init__("Type")

        self.runtime_type = self

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return is_type(target.runtime_type)

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return is_type(source.runtime_type)

    def __repr__(self):
        return "type"


Type = _Type()
del _Type


class _TypeBase(Class):
    def __init__(self, name: str):
        super().__init__(name)

        self.runtime_type = Type

        self.base = Type

    def assignable_to(self, target: "TypeProtocol") -> bool:
        raise NotImplementedError

    def assignable_from(self, source: "TypeProtocol") -> bool:
        raise NotImplementedError


class _Void(_TypeBase):
    def __init__(self):
        super().__init__("Void")

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
        super().__init__("Unit")

        self.UnitInstance = self._Unit(self)

        constructor = Method(return_type=self, binding=Binding.Static)
        constructor.body.instructions.extend([
            vm.LoadObject(self.UnitInstance),
            vm.Return()
        ])

        self.constructors.append(constructor)
        self.fields.append(Field("unit", self, self.UnitInstance, Binding.Static, Access.Constant))

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
        super().__init__("Boolean")

        self.TrueInstance = self._Boolean(True, self)
        self.FalseInstance = self._Boolean(False, self)

        self.fields.append(Field("true", self, self.TrueInstance, Binding.Static, Access.Constant))
        self.fields.append(Field("false", self, self.FalseInstance, Binding.Static, Access.Constant))

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
        super().__init__("any")

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
        super().__init__("NullType")

        self.NullInstance = self._Null(self)

        self.fields.append(Field("null", self, self.NullInstance, Binding.Static, Access.Constant))

        del _Null._Null

    def assignable_to(self, target: "TypeProtocol") -> bool:
        return isinstance(target, Nullable)

    def assignable_from(self, source: "TypeProtocol") -> bool:
        return source is _Null

    def __repr__(self):
        return "nulltype"


Null = _Null()
del _Null


# class _FunctionType(GenericClass):
#     """
#     This is the type of all functions. This class is a template that can be instantiated to fit a certain signature.
#
#     Z# source code:
#
#     class Function(return_type: type, variadic_positional: Parameter?, variadic_named: Parameter?, *parameters: Parameter) {
#         ?
#     }
#     """
#
#     def __init__(self):
#         super().__init__("FunctionType", Type)


del _TypeBase


Class.runtime_type = Type


if __name__ == '__main__':
    print("Type:", Type)
    print("Void:", Void)
    print("Unit:", Unit)
    print("Unit.UnitInstance:", Unit.UnitInstance)
    print("Boolean:", Boolean)
    print("Boolean.TrueInstance:", Boolean.TrueInstance)
    print("Boolean.FalseInstance:", Boolean.FalseInstance)
    print("Any:", Any)
    print("Any.UndefinedInstance:", Any.UndefinedInstance)
    print("Null:", Null)
    print("Null.NullInstance:", Null.NullInstance)

    print("Nullable(Boolean):", Nullable(Boolean))
    print("bool? <- bool ::", assignable_to(Boolean, Nullable(Boolean)))
    print("bool <- bool? ::", assignable_from(Boolean, Nullable(Boolean)))

    print("Runtime Type == Type:", Type is Type.runtime_type is Void.runtime_type is Unit.runtime_type is Boolean.runtime_type is Any.runtime_type is Null.runtime_type)
    print("Base == Type: ", Type is Void.base is Unit.base is Boolean.base is Any.base is Null.base)
