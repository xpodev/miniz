from typing import TypeVar, Callable, TypeAlias

from miniz.generic.generic_construction import IConstructor
from miniz.generic.function import GenericFunction
from miniz.generic.signature import GenericParameter, GenericSignature, GenericArguments
from miniz.oop import Binding, Access, Method, Field, Property, Class, Typeclass, Interface
from miniz.scope import Scope
from miniz.signature import Parameter, Signature
from miniz.type_system import ImplementsType, ObjectProtocol, Any
from utils import NotifyingList

_T = TypeVar("_T")
_GenericT = TypeVar("_GenericT")


def order_arguments(args: GenericArguments, signature: Signature | GenericSignature) -> tuple:
    ordered = []
    for parameter in signature.positional_parameters:
        if parameter in args:
            ordered.append(args[parameter])

    for parameter in signature.named_parameters:
        if parameter in args:
            ordered.append(args[parameter])

    if signature.variadic_positional_parameter in args:
        ordered.append(args[signature.variadic_positional_parameter])

    if signature.variadic_named_parameter in args:
        ordered.append(args[signature.variadic_named_parameter])

    return tuple(ordered)


class Member:
    name: str | None
    binding: Binding
    owner: "GenericClass | None"

    def __init__(self, name: str | None, binding: Binding = Binding.Instance):
        self.name = name
        self.binding = binding


class GenericField(IConstructor[Field], Member):
    type: ImplementsType | Parameter | GenericParameter
    default_value: ObjectProtocol | None
    access: Access

    def __init__(self, name: str, type: ImplementsType | Parameter | GenericParameter = Any, default_value: ObjectProtocol = None, binding: Binding = Binding.Instance,
                 access: Access = Access.ReadWrite):
        super().__init__(name, binding)
        self.type = type
        self.default_value = default_value
        self.access = access

    def construct(self, args: dict[Parameter, ObjectProtocol], factory=None, generic_factory=None) -> "Field | GenericField":
        type = args.get(self.type, self.type.construct(args) if isinstance(self.type, GenericParameter) else self.type)
        default_value = self.default_value  # todo: generic eval default value

        if isinstance(type, (GenericParameter, Parameter)):
            result = (generic_factory or GenericField)(self.name, type, default_value)
        else:
            assert isinstance(type, ImplementsType)
            result = (factory or Field)(self.name, type, default_value)

        result.binding = self.binding
        result.access = self.access

        return result

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
        return f"{declare} {self.name}[{self.binding}]"
        return f"{declare} {self.name}[{self.binding.name}]: {self.type}" + (f" = {self.default_value}" if self.default_value is not None else '') + ';'


class GenericMethod(GenericFunction, Member):
    def __init__(self, lexical_scope: Scope | None, name: str = None, return_type: ImplementsType | Parameter | GenericParameter = Any, binding: Binding = Binding.Instance):
        GenericFunction.__init__(self, lexical_scope, name, return_type)
        Member.__init__(self, name, binding)

    def construct(self, args: dict[Parameter, ObjectProtocol], factory=None, generic_factory=None) -> "Method | GenericMethod":
        result = super().construct(args, Method, GenericMethod)

        result.binding = self.binding

        return result

    def __repr__(self):
        return f"{self.signature} [{self.binding.name}] {{}}"


class GenericProperty(IConstructor[Property], Member):
    type: ImplementsType | Parameter | GenericParameter
    default_value: ObjectProtocol | None

    _getter: GenericMethod | None
    _setter: GenericMethod | None

    def __init__(self, name: str, type: ImplementsType | Parameter | GenericParameter = Any, default_value: ObjectProtocol = None, binding: Binding = Binding.Instance):
        super().__init__(name, binding)
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

    def construct(self, args: dict[Parameter, ObjectProtocol], factory=None, generic_factory=None) -> Property:
        type = args.get(self.type, self.type.construct(args) if isinstance(self.type, GenericParameter) else self.type)
        default_value = self.default_value  # todo: generic eval default value

        if isinstance(type, (Parameter, GenericParameter)):
            result = (generic_factory or GenericProperty)(self.name, type, default_value)
        else:
            assert isinstance(type, ImplementsType)
            result = (factory or Property)(self.name, type, default_value)

        result.binding = self.binding

        return result

    def __repr__(self):
        return f"let {self.name}[{self.binding.name}]: {self.type} => {{{f' get = {self._getter.name};' if self._getter else ''}{f' set = {self._setter.name};' if self._setter else ''} }}" + (
            f" = {self.default_value}" if self.default_value is not None else '') + ';'


class GenericOOPObject(IConstructor["ConstructedClass | ConstructedInterface | ConstructedTypeclass"]):
    _members: dict[str, Member]
    _member_list: list[Member]

    _fields: NotifyingList[GenericField | Field]
    _methods: NotifyingList[GenericMethod | Method]
    _properties: NotifyingList[GenericProperty | Property]
    _constructors: NotifyingList[GenericMethod | Method]

    _signature: Signature | GenericSignature

    _cache: dict[tuple, "GenericClass | ConstructedClass"]

    constructor: "GenericClass | GenericInterface | GenericTypeclass"
    arguments: dict[Parameter | GenericParameter, Parameter | GenericParameter | ObjectProtocol]

    def __init__(self, name_or_signature: str | Signature | GenericSignature, constructor: "GenericClass" = None, arguments: GenericArguments = None):
        if name_or_signature is None or isinstance(name_or_signature, str):
            self._signature = GenericSignature(name_or_signature)
        else:
            self._signature = name_or_signature

        self._members = {}
        self._member_list = []

        self._base = None
        self._interfaces = []

        self.constructor = constructor
        if constructor:
            self.arguments = arguments or {}
        else:
            self.arguments = arguments
        self._cache = getattr(constructor, "_cache", {})

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

        self.on_add_member = on_add_member
        self.on_remove_member = on_remove_member

    @property
    def name(self):
        return self.signature.name

    @name.setter
    def name(self, value):
        self.signature.name = value

    @property
    def cache(self):
        return self._cache

    @property
    def signature(self):
        return self._signature

    @signature.setter
    def signature(self, value: Signature | GenericSignature):
        self._signature = value

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

    def construct(
            self,
            args: dict[Parameter, ObjectProtocol],
            factory: Callable[[], "_T | Class | ConstructedClass | Interface | ConstructedInterface | Typeclass | ConstructedTypeclass"] = None,
            generic_factory: Callable[[], "_GenericT | GenericClass | GenericInterface | GenericTypeclass"] = None,
            *,
            enable_caching: bool = True
    ) -> _T | _GenericT:
        ordered_arguments = order_arguments(args, self.signature)  # PyCharm wouldn't let me put it inside because of the usage below (which is safe!)
        if enable_caching:
            if ordered_arguments in self.cache:
                return self.cache[ordered_arguments]

        signature = self.signature
        if isinstance(signature, IConstructor):
            signature = signature.construct(args)
        if not any([signature.positional_parameters, signature.named_parameters, signature.variadic_positional_parameter, signature.variadic_named_parameter]):
            signature = Signature(self.name)

        fields = []
        for field in self.fields:
            result = field
            if isinstance(field, GenericField):
                result = field.construct(args)
            fields.append(result)

        methods = []
        for method in self.methods:
            result = method
            if isinstance(method, GenericMethod):
                result = method.construct(args)
            methods.append(result)

        props = []
        for prop in self.properties:
            result = prop
            if isinstance(prop, GenericProperty):
                result = prop.construct(args)
            props.append(result)

        if any(
                isinstance(item, IConstructor) for item in [signature, *fields, *methods, *props]
        ):
            result = (generic_factory or GenericClass)(signature, constructor=self.constructor or self, arguments=args)
        else:
            result = (factory or ConstructedClass)(self.name, constructor=self.constructor or self, arguments=args)

        for field in fields:
            result.fields.append(field)
        for method in methods:
            result.methods.append(method)
        for prop in props:
            result.properties.append(prop)

        if enable_caching:
            self.cache[ordered_arguments] = result

        return result


class GenericClass(GenericOOPObject, ImplementsType):
    _base: "Class | GenericClass | ConstructedClass | None"

    _interfaces: list["GenericInterface | Interface"]

    _nested_classes_and_interfaces: NotifyingList["GenericNestedClass | GenericNestedInterface | NestedClass | NestedInterface"]

    def __init__(self, name_or_signature: str | Signature | GenericSignature, base: "Class | GenericClass | ConstructedClass | None" = None, constructor: "GenericClass" = None,
                 arguments: GenericArguments = None):
        super().__init__(name_or_signature, constructor, arguments)

        self._base = base

        self._interfaces = []

        self._nested_classes_and_interfaces = NotifyingList()

        self._nested_classes_and_interfaces.append += self.on_add_member
        self._nested_classes_and_interfaces.pop += self.on_remove_member
        self._nested_classes_and_interfaces.remove += self.on_remove_member

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
    def nested_classes_and_interfaces(self):
        return self._nested_classes_and_interfaces

    def assignable_to(self, target: ImplementsType) -> bool:
        return target is self

    def assignable_from(self, source: ImplementsType) -> bool:
        if source is self:
            return True

        if isinstance(source, ConstructedClass):
            return source.constructor is self

        return False

    def construct(
            self,
            args: dict[Parameter | GenericParameter, ObjectProtocol | Parameter | GenericParameter],
            factory: Callable[[], _T | Class] = None,
            generic_factory: Callable[[], "_GenericT | GenericClass"] = None,
            **kwargs
    ) -> _T | _GenericT:
        ordered_arguments = order_arguments(args, self.signature)
        if ordered_arguments in self.cache:
            return self.cache[ordered_arguments]

        base = self.base
        if isinstance(base, IConstructor):
            base = base.construct(args)

        interfaces = []
        for interface in self.interfaces:
            result = interface
            if isinstance(interface, GenericInterface):
                result = interface.construct(args)
            interfaces.append(result)

        if any(isinstance(item, IConstructor) for item in [base, *interfaces]):
            factory = GenericClass

        result = super().construct(args, factory or ConstructedClass, generic_factory or GenericClass, **kwargs)

        result.base = base

        for interface in interfaces:
            result.interfaces.append(interface)

        for nested_class_or_interface in self._nested_classes_and_interfaces:
            if isinstance(nested_class_or_interface, IConstructor):
                result.nested_classes_and_interfaces.append(nested_class_or_interface.construct(args, **kwargs))
            else:
                result.nested_classes_and_interfaces.append(nested_class_or_interface)

        return result

    def __repr__(self):
        return f"class {self.signature}"
        declaration = \
            f"class{' ' if self.name else ''}{self.signature} " \
            f"{(f'< ' + ', '.join(base.name for base in [*((self._base,) if self._base is not None else ()), *self._interfaces]) + ' ') if self.base is not None or self._interfaces else ''}{{ "

        members = "".join(map(lambda m: "\n\t" + repr(m), self._member_list))

        if members:
            return declaration + members + "\n}"
        return declaration + '}'


class GenericInterface(GenericOOPObject):
    _bases: list["Interface | GenericInterface | ConstructedInterface"]

    def __init__(self, name_or_signature: str | Signature | GenericSignature, constructor: "GenericClass" = None):
        super().__init__(name_or_signature, constructor)

        self._bases = []

        self._nested_classes_and_interfaces = NotifyingList()

        self._nested_classes_and_interfaces.append += self.on_add_member
        self._nested_classes_and_interfaces.pop += self.on_remove_member
        self._nested_classes_and_interfaces.remove += self.on_remove_member

    @property
    def bases(self):
        return self._bases

    @property
    def nested_classes_and_interfaces(self):
        return self._nested_classes_and_interfaces

    def construct(
            self,
            args: dict[Parameter | GenericParameter, ObjectProtocol | Parameter | GenericParameter],
            factory: Callable[[], "_T | Interface | ConstructedInterface"] = None,
            generic_factory: Callable[[], "IConstructor[_T] | GenericInterface"] = None,
            **kwargs
    ) -> "_T | IConstructor[_T]":
        bases = []
        for base in self.bases:
            if isinstance(base, IConstructor):
                base = base.construct(args)
            bases.append(base)

        if any(isinstance(base, IConstructor) for base in bases):
            factory = GenericInterface

        result = super().construct(args, factory or ConstructedInterface, generic_factory or GenericInterface, **kwargs)

        for base in bases:
            result.bases.append(base)

        for nested_class_or_interface in self._nested_classes_and_interfaces:
            if isinstance(nested_class_or_interface, IConstructor):
                result.nested_classes_and_interfaces.append(nested_class_or_interface.construct(args, **kwargs))
            else:
                result.nested_classes_and_interfaces.append(nested_class_or_interface)

        return result

    def __repr__(self):
        declaration = f"interface{' ' if self.name else ''}{self.signature} {(f'< ' + ', '.join(base.name for base in self._bases) + ' ') if self.bases else ''}{{"

        members = "".join(map(lambda m: "\n\t" + repr(m), self._member_list))

        if members:
            return declaration + members + "\n}"
        return declaration + '}'


class GenericTypeclass(GenericOOPObject):
    _bases: list["Typeclass | ConstructedTypeclass | GenericTypeclass"]

    def __init__(self, name_or_signature: str | Signature | GenericSignature, constructor: "GenericClass" = None):
        super().__init__(name_or_signature, constructor)

        self._bases = []

    @property
    def bases(self):
        return self._bases

    def construct(
            self,
            args: dict[Parameter | GenericParameter, ObjectProtocol | Parameter | GenericParameter],
            factory: Callable[[], "_T | Typeclass | ConstructedTypeclass"] = None,
            generic_factory: Callable[[], "IConstructor[_T] | GenericTypeclass"] = None,
            **kwargs
    ) -> "_T | IConstructor[_T]":
        bases = []
        for base in self.bases:
            if isinstance(base, IConstructor):
                base = base.construct(args)
            bases.append(base)

        if any(isinstance(base, IConstructor) for base in bases):
            factory = GenericTypeclass

        result = super().construct(args, factory or ConstructedTypeclass, generic_factory or GenericTypeclass, **kwargs)

        for base in bases:
            result.bases.append(base)

        return result

    def __repr__(self):
        declaration = f"typeclass{' ' if self.name else ''}{self.signature} {(f'< ' + ', '.join(base.name for base in self._bases) + ' ') if self.bases else ''}{{"

        members = "".join(map(lambda m: "\n\t" + repr(m), self._member_list))

        if members:
            return declaration + members + "\n}"
        return declaration + '}'


class ConstructedClass(Class):
    def __init__(self, name: str, constructor: GenericClass, arguments: dict[Parameter | GenericParameter, ObjectProtocol]):
        super().__init__(name)
        self.constructor = constructor
        self.arguments = arguments


class ConstructedInterface(Interface):
    def __init__(self, name: str, constructor: GenericInterface):
        super().__init__(name)
        self.constructor = constructor


class ConstructedTypeclass(Typeclass):
    def __init__(self, name: str, constructor: GenericTypeclass):
        super().__init__(name)
        self.constructor = constructor


if __name__ == '__main__':
    from miniz.type_system import Type, Boolean

    iiterable = GenericInterface("IIterable")
    _T = Parameter("T", Type)
    iiterable.signature.positional_parameters.append(_T)

    iiterator = GenericInterface("IIterator")
    _IteratorT = Parameter("T", Type)
    iiterator.signature.positional_parameters.append(_IteratorT)

    iiterable_get_iterator = GenericMethod(None, "get_iterator", _T)
    # iiterable_get_iterator = GenericMethod(None, "get_iterator", iiterator.construct({_IteratorT: _T}))
    iiterable.methods.append(iiterable_get_iterator)

    print(iiterable)

    list_class_signature = GenericSignature("List")
    T = Parameter("T", Type)
    list_class_signature.positional_parameters.append(T)

    list_class = GenericClass(list_class_signature)

    list_class.interfaces.append(iiterable.construct({_T: T}))

    list_add = GenericMethod(None, "add", Boolean)
    list_add.positional_parameters.append(GenericParameter("item", T))

    list_length = Property("is_empty", Boolean)

    list_class.methods.append(list_add)
    list_class.properties.append(list_length)

    print(list_class)

    list_of_types = list_class.construct({T: Boolean})

    print(list_of_types)

    list_of_types.methods[0].binding = Binding.Class

    print(list_of_types)

    print(list_class.construct({T: Boolean}))

    print(list_class.construct({T: Type}))

    print(list_class.interfaces[0])
    print(list_of_types.interfaces[0])
