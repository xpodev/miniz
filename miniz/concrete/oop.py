from dataclasses import dataclass
from enum import Enum

import miniz.ownership
from miniz.concrete.function import Function
from miniz.concrete.overloading import OverloadGroup
from miniz.interfaces.base import ScopeProtocol
from miniz.interfaces.function import IFunction
from miniz.interfaces.oop import Binding, IOOPMember, IField, IMethod, IProperty, IClass, IInterface, ITypeclass, OOPImplementable, IOOPDefinition
from miniz.core import ImplementsType, ObjectProtocol, TypeProtocol
from utils import NotifyingList
from zs.zs2miniz.lib import Scope


class Access(Enum):
    ReadOnly = "ReadOnly"
    ReadWrite = "ReadWrite"
    Constant = "Constant"


class Member(IOOPMember):
    def __init__(self, name: str | None, binding: Binding = Binding.Instance):
        super().__init__()
        self.name = name
        self.binding = binding


class Field(Member, IField):
    field_type: ImplementsType
    default_value: ObjectProtocol | None
    access: Access

    def __init__(self, name: str, type: ImplementsType = None, default_value: ObjectProtocol = None, binding: Binding = Binding.Instance, access: Access = Access.ReadWrite):
        super().__init__(name, binding)
        self.field_type = type
        self.default_value = default_value
        self.access = access

    @property
    def index(self):
        if self.owner is None:
            raise ValueError(f"Field {self} doesn't have an owner")
        return self.owner.fields.index(self)

    def __repr__(self):
        match self.access:
            case Access.ReadWrite:
                declare = "var"
            case Access.ReadOnly:
                declare = "let"
            case Access.Constant:
                declare = "const"
            case _:
                raise ValueError(self.access)
        return f"{declare} {self.name}[{self.binding.name}]"
        # return f"{declare} {self.name}[{self.binding.name}]: {self.type.reference_representation()}" + (f" = {self.default_value}" if self.default_value is not None else '') + ';'


class Method(Function, Member, IMethod):
    def __init__(self, name: str = None, return_type: ImplementsType = None, binding: Binding = Binding.Instance):
        Function.__init__(self, name, return_type)
        Member.__init__(self, name, binding)
        IMethod.__init__(self)

    # def __repr__(self):
    #     return f"{self.signature} [{self.binding.name}] {{}}"


class Property(Member, IProperty):
    type: ImplementsType
    default_value: ObjectProtocol | None

    _getter: Method | None
    _setter: Method | None

    def __init__(self, name: str, type: ImplementsType = None, default_value: ObjectProtocol = None, binding: Binding = Binding.Instance):
        super().__init__(name, binding)
        IProperty.__init__(self)
        self.type = type
        self.default_value = default_value

        self._getter = self._setter = None

    @property
    def getter(self):
        return self._getter

    @getter.setter
    def getter(self, value: Method | None):
        if value is not None and value.binding != self.binding:
            raise ValueError(f"Property getter must have the same binding as the property itself")
        self._getter = value

    @property
    def setter(self):
        return self._setter

    @setter.setter
    def setter(self, value):
        if value is not None and value.binding != self.binding:
            raise ValueError(f"Property setter must have the same binding as the property itself")
        self._setter = value

    def __repr__(self):
        return f"let {self.name}[{self.binding.name}]: {self.type} => {{{f' get = {self._getter.name};' if self._getter else ''}{f' set = {self._setter.name};' if self._setter else ''} }}" + (
            f" = {self.default_value}" if self.default_value is not None else '') + ';'


class Class(IClass, TypeProtocol, ScopeProtocol):
    as_member: miniz.ownership.Member["Class"]

    name: str | None

    _scope: Scope

    _base: "Class | None"
    _interfaces: list["Interface"]

    _fields: NotifyingList[IField]
    _methods: NotifyingList[IMethod]
    _properties: NotifyingList[IProperty]
    _constructors: NotifyingList[IMethod]

    _nested_classes_and_interfaces: NotifyingList["NestedClass | NestedInterface"]

    def __init__(self, name: str | None = None):
        super().__init__()
        self.name = name
        self.runtime_type = IOOPDefinition.runtime_type_constructor(self)

        self._scope = Scope()

        self._base = None
        self._interfaces = []

        self._fields = NotifyingList()
        self._methods = NotifyingList()
        self._properties = NotifyingList()

        self._constructor = OverloadGroup(f"{name or '{AnonymousClass}'}::Constructor", None, owner=self)
        self._constructor.overloads = self._constructors = NotifyingList()

        self._nested_classes_and_interfaces = NotifyingList()

        def on_add_member(ms, member: Member):
            if member.owner is not None:
                raise TypeError

            if isinstance(member, IFunction):
                if not isinstance(member, IMethod):
                    raise TypeError
                if ms is not self.constructors and member.name:
                    group = self._scope.lookup_name(member.name, recursive_lookup=False, default=None)
                    if group is None:
                        group = OverloadGroup(member.name, None, owner=self)
                        self._scope.create_name(group.name, group)
                member.owner = self
                return
            if member.name:
                self._scope.create_name(member.name, member)
            member.owner = self

        def on_remove_member(ms, member: int | Member):
            if isinstance(member, int):
                member = ms[member]
            if member.name:
                if ms is self.methods:
                    if ms is self.methods:
                        group = self._scope.lookup_name(member.name)
                        assert isinstance(group, OverloadGroup)
                        group.overloads.remove(member)
                self._scope.delete_name(member.name)
            member.owner = None

        self._fields.append += on_add_member
        self._methods.append += on_add_member
        self._properties.append += on_add_member
        self._constructors.append += on_add_member

        self._nested_classes_and_interfaces.append += on_add_member

        self._fields.pop += on_remove_member
        self._methods.pop += on_remove_member
        self._properties.pop += on_remove_member
        self._constructors.pop += on_remove_member

        self._nested_classes_and_interfaces.pop += on_remove_member

        self._fields.remove += on_remove_member
        self._methods.remove += on_remove_member
        self._properties.remove += on_remove_member
        self._constructors.remove += on_remove_member

        self._nested_classes_and_interfaces.remove += on_remove_member

    @property
    def base(self):
        return self._base

    @base.setter
    def base(self, value: "Class | None"):
        self._base = value

    @property
    def interfaces(self):
        return self._interfaces

    @property
    def specifications(self):
        return self._interfaces

    @property
    def fields(self):
        return self._fields

    @property
    def methods(self):
        return self._methods

    @property
    def properties(self):
        return self._properties

    @property
    def constructor(self):
        return self._constructor

    @property
    def constructors(self):
        return self._constructors

    @property
    def nested_definitions(self):
        return self._nested_classes_and_interfaces

    def assignable_from(self, source: "TypeProtocol") -> bool:
        if isinstance(source, Class):
            return source.is_subclass_of(self)
        return bool(self.constructor.get_match([self, source], [], strict=True, recursive=False))

    def assignable_to(self, target: "TypeProtocol") -> bool:
        if isinstance(target, Class):
            return self.is_subclass_of(target)
        if isinstance(target, OOPImplementable):
            base = self
            while base is not None:
                if target.is_implemented(self):
                    return True
                base = base.base
        return target.assignable_from(self)

    def is_subclass_of(self, other: "Class"):
        base = self
        while base is not None:
            if other == base:
                return True
            base = base.base
        return False

    def is_base_class_of(self, other: "Class"):
        return other.is_subclass_of(self)

    def get_name(self, name: str) -> ObjectProtocol:
        base = self
        result = None
        while result is None and base is not None:
            result = base._scope.lookup_name(name, default=None)
            base = base.base
        return result

    def __repr__(self):
        return f"class {self.name or '{Anonymous}'}"

        # declaration = \
        #     f"class{(' ' + self.name) if self.name else ''} " \
        #     f"{(f'< ' + ', '.join(base.name for base in [*((self._base,) if self._base is not None else ()), *self._interfaces]) + ' ') if self.base is not None or self._interfaces else ''}{{ "
        #
        # members = "".join(map(lambda m: "\n\t" + repr(m), self._member_list))
        #
        # if members:
        #     return declaration + members + "\n}"
        # return declaration + '}'


class Interface(IInterface):
    name: str | None

    _members: dict[str, Member]
    _member_list: list[Member]

    _bases: list["Interface"]

    _fields: NotifyingList[Field]
    _methods: NotifyingList[Method]
    _properties: NotifyingList[Property]
    _constructors: NotifyingList[Method]

    # _constructor: GenericOverload[Method]  todo

    _nested_classes_and_interfaces: NotifyingList["Class"]

    def __init__(self, name: str | None = None):
        super().__init__()
        self.name = name

        self._members = {}
        self._member_list = []

        self._bases = []

        self._fields = NotifyingList()
        self._methods = NotifyingList()
        self._properties = NotifyingList()
        self._constructors = NotifyingList()

        self._nested_classes_and_interfaces = NotifyingList()

        def on_add_member(ms, member: Member):
            if ms is self._constructors:
                if not isinstance(member, Method):
                    raise TypeError(f"Constructor must be a method, got {type(member)}")
                # self._constructor.overloads.append(member)  todo (or not)
                member.owner = self
            if member.name and not isinstance(member, Method) and member.name in self._members or isinstance(member, Method) and not isinstance(self._members.get(member.name, member), Method):
                raise ValueError(f"Class {self.name} already defines member \'{member.name}\'")
            if member.name and member.name not in self._members:
                self._members[member.name] = member
            self._member_list.append(member)
            member.owner = self

        def on_remove_member(ms, member: int | Member):
            if isinstance(member, int):
                member = ms[member]
            if member.name:
                if isinstance(member, Method):
                    ...  # todo: overload support
                else:
                    del self._members[member.name]
            self._member_list.remove(member)
            member.owner = None

        self._fields.append += on_add_member
        self._methods.append += on_add_member
        self._properties.append += on_add_member
        self._constructors.append += on_add_member

        self._nested_classes_and_interfaces.append += on_add_member

        self._fields.pop += on_remove_member
        self._methods.pop += on_remove_member
        self._properties.pop += on_remove_member
        self._constructors.pop += on_remove_member

        self._nested_classes_and_interfaces.pop += on_remove_member

        self._fields.remove += on_remove_member
        self._methods.remove += on_remove_member
        self._properties.remove += on_remove_member
        self._constructors.remove += on_remove_member

        self._nested_classes_and_interfaces.remove += on_remove_member

    @property
    def bases(self):
        return self._bases

    @property
    def fields(self):
        return self._fields

    @property
    def methods(self):
        return self._methods

    @property
    def properties(self):
        return self._properties

    @property
    def constructors(self):
        return self._constructors

    @property
    def nested_classes_and_interfaces(self):
        return self._nested_classes_and_interfaces

    def __repr__(self):
        declaration = f"interface{(' ' + self.name) if self.name else ''} {(f'< ' + ', '.join(base.name for base in self._bases) + ' ') if self.bases else ''}{{"

        members = "".join(map(lambda m: "\n\t" + repr(m), self._member_list))

        if members:
            return declaration + members + "\n}"
        return declaration + '}'


@dataclass(slots=True)
class TypeclassImplementation:
    typeclass: "Typeclass"
    type: ImplementsType
    implementation: Class

    def __repr__(self):
        return f"typeclass {self.typeclass.name}({self.type.name if isinstance(self.type, (Class, Interface, Typeclass)) else self.type});"


class Typeclass(ITypeclass):
    name: str | None

    _members: dict[str, Member]
    _member_list: list[Member]

    _bases: list["Typeclass"]

    _fields: NotifyingList[Field]
    _methods: NotifyingList[Method]
    _properties: NotifyingList[Property]
    _constructors: NotifyingList[Method]

    _implementations: dict[ImplementsType, TypeclassImplementation]

    # _constructor: GenericOverload[Method]  todo

    def __init__(self, name: str | None = None):
        super().__init__()
        self.name = name

        self._members = {}
        self._member_list = []

        self._bases = []

        self._fields = NotifyingList()
        self._methods = NotifyingList()
        self._properties = NotifyingList()
        self._constructors = NotifyingList()

        def on_add_member(ms, member: Member):
            if ms is self._constructors:
                if not isinstance(member, Method):
                    raise TypeError(f"Constructor must be a method, got {type(member)}")
                # self._constructor.overloads.append(member)  todo (or not)
                member.owner = self
            if member.name and not isinstance(member, Method) and member.name in self._members or isinstance(member, Method) and not isinstance(self._members.get(member.name, member), Method):
                raise ValueError(f"Class {self.name} already defines member \'{member.name}\'")
            if member.name and member.name not in self._members:
                self._members[member.name] = member
            self._member_list.append(member)
            member.owner = self

        def on_remove_member(ms, member: int | Member):
            if isinstance(member, int):
                member = ms[member]
            if member.name:
                if isinstance(member, Method):
                    ...  # todo: overload support
                else:
                    del self._members[member.name]
            self._member_list.remove(member)
            member.owner = None

        self._fields.append += on_add_member
        self._methods.append += on_add_member
        self._properties.append += on_add_member
        self._constructors.append += on_add_member

        self._fields.pop += on_remove_member
        self._methods.pop += on_remove_member
        self._properties.pop += on_remove_member
        self._constructors.pop += on_remove_member

        self._fields.remove += on_remove_member
        self._methods.remove += on_remove_member
        self._properties.remove += on_remove_member
        self._constructors.remove += on_remove_member

    @property
    def bases(self):
        return self._bases

    @property
    def fields(self):
        return self._fields

    @property
    def methods(self):
        return self._methods

    @property
    def properties(self):
        return self._properties

    @property
    def constructors(self):
        return self._constructors

    def add_implementation(self, type: ImplementsType, implementation_class: Class):
        if type in self._implementations:
            type_name = type.name if isinstance(type, (Class, Interface, Typeclass)) else type
            raise TypeError(f"Typeclass {self.name} is already implemented for type {type_name}")
        self._implementations[type] = TypeclassImplementation(self, type, implementation_class)

    def remove_implementation(self, type: ImplementsType):
        if type not in self._implementations:
            type_name = type.name if isinstance(type, (Class, Interface, Typeclass)) else type
            raise TypeError(f"Type {type_name} does not implement typeclass {self.name}")

    def __repr__(self):
        declaration = f"typeclass{(' ' + self.name) if self.name else ''} {(f'< ' + ', '.join(base.name for base in self._bases) + ' ') if self.bases else ''}{{"

        members = "".join(map(lambda m: "\n\t" + repr(m), self._member_list))

        if members:
            return declaration + members + "\n}"
        return declaration + '}'


if __name__ == '__main__':
    from miniz.type_system import Void

    fieldA = Field("A")

    print(fieldA)

    methodB = Method("B")

    print(methodB)

    propertyC = Property("C")

    print(propertyC)

    propertyC.getter = methodB

    print(propertyC)

    propertyC.setter = methodB

    print(propertyC)

    propertyC.getter = None

    print(propertyC)

    classFoo = Class("Foo")

    print(classFoo)

    classFoo.fields.append(fieldA)
    classFoo.methods.append(methodB)
    classFoo.properties.append(propertyC)

    try:
        classFoo.methods.append(Method("A"))
    except ValueError as e:
        print("Exception", e.args)
    else:
        raise TypeError(f"expected an exception to be raised!")

    fieldA.binding = Binding.Static

    print(classFoo)

    classBar = Class("Bar")

    classBar.base = classFoo

    print(classBar)

    classFoo.nested_definitions.append(classBar)

    print(classFoo)

    interfaceIFoo = Interface("IFoo")
    interfaceIFoo.bases.append(interfaceIFoo)

    interfaceIFoo.methods.append(Method("do_foo", Void))

    print(interfaceIFoo)

    classFoo.interfaces.append(interfaceIFoo)

    print(classFoo)
