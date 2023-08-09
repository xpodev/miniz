from typing import TypeVar, Callable, Generic

from miniz.template.template_construction import IConstructor
from miniz.template.function import FunctionTemplate
from miniz.template.signature import ParameterTemplate, SignatureTemplate, GenericArguments
from miniz.concrete.oop import Binding, Access, Method, Field, Property, Class, Typeclass, Interface, Member
from miniz.concrete.signature import Parameter, Signature
from miniz.interfaces.oop import IField, IMethod, IProperty, IOOPDefinition
from miniz.type_system import TypeProtocol, ObjectProtocol, Any
from utils import NotifyingList

_T = TypeVar("_T")
_GenericT = TypeVar("_GenericT")


def order_arguments(args: GenericArguments, signature: Signature | SignatureTemplate) -> tuple:
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


class FieldTemplate(Member, IConstructor[Field], IField):
    field_type: TypeProtocol | Parameter | ParameterTemplate
    default_value: ObjectProtocol | None
    access: Access

    def __init__(self, name: str, type: TypeProtocol | Parameter | ParameterTemplate = Any, default_value: ObjectProtocol = None, binding: Binding = Binding.Instance,
                 access: Access = Access.ReadWrite):
        Member.__init__(self, name, binding)
        IField.__init__(self)
        self.field_type = type
        self.default_value = default_value
        self.access = access

    def construct(self, args: dict[Parameter, ObjectProtocol], factory=None, generic_factory=None) -> "Field | GenericField":
        type = args.get(self.field_type, self.field_type.construct(args) if isinstance(self.field_type, ParameterTemplate) else self.field_type)
        default_value = self.default_value  # todo: generic eval default value

        if isinstance(type, (ParameterTemplate, Parameter)):
            result = (generic_factory or FieldTemplate)(self.name, type, default_value)
        else:
            assert isinstance(type, TypeProtocol)
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
        # return f"{declare} {self.name}[{self.binding.name}]: {self.field_type}" + (f" = {self.default_value}" if self.default_value is not None else '') + ';'


class MethodTemplate(FunctionTemplate, IMethod, Member):
    def __init__(self, name: str = None, return_type: TypeProtocol | Parameter | ParameterTemplate = Any, binding: Binding = Binding.Instance):
        FunctionTemplate.__init__(self, name, return_type)
        IMethod.__init__(self)
        Member.__init__(self, name, binding)

    def construct(self, args: dict[Parameter, ObjectProtocol], factory=None, generic_factory=None) -> "Method | GenericMethod":
        result = super().construct(args, factory=Method, generic_factory=MethodTemplate)

        result.binding = self.binding

        return result

    def __repr__(self):
        return f"{self.signature} [{self.binding.name}] {{}}"


class PropertyTemplate(Member, IConstructor[Property], IProperty):
    property_type: TypeProtocol | Parameter | ParameterTemplate
    default_value: ObjectProtocol | None

    _getter: MethodTemplate | None
    _setter: MethodTemplate | None

    def __init__(self, name: str, type: TypeProtocol | Parameter | ParameterTemplate = Any, default_value: ObjectProtocol = None, binding: Binding = Binding.Instance):
        Member.__init__(self, name, binding)
        IProperty.__init__(self)

        self.property_type = type
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
        type = args.get(self.property_type, self.property_type.construct(args) if isinstance(self.property_type, ParameterTemplate) else self.property_type)
        default_value = self.default_value  # todo: generic eval default value

        if isinstance(type, (Parameter, ParameterTemplate)):
            result = (generic_factory or PropertyTemplate)(self.name, type, default_value)
        else:
            assert isinstance(type, TypeProtocol)
            result = (factory or Property)(self.name, type, default_value)

        result.binding = self.binding

        return result

    def __repr__(self):
        return f"let {self.name}[{self.binding.name}]: {self.property_type} => {{{f' get = {self._getter.name};' if self._getter else ''}{f' set = {self._setter.name};' if self._setter else ''} }}" + (
            f" = {self.default_value}" if self.default_value is not None else '') + ';'


class OOPObjectTemplate(IOOPDefinition, IConstructor["ConstructedClass | ConstructedInterface | ConstructedTypeclass"]):
    _members: dict[str, Member]
    _member_list: list[Member]

    _fields: NotifyingList[FieldTemplate | Field]
    _methods: NotifyingList[MethodTemplate | Method]
    _properties: NotifyingList[PropertyTemplate | Property]
    _constructors: NotifyingList[MethodTemplate | Method]

    _signature: Signature | SignatureTemplate

    _cache: dict[tuple, "GenericClass | ConstructedClass"]

    constructor: "GenericClass | GenericInterface | GenericTypeclass"
    arguments: dict[Parameter | ParameterTemplate, Parameter | ParameterTemplate | ObjectProtocol]

    def __init__(self, name_or_signature: str | Signature | SignatureTemplate, constructor: "ClassTemplate" = None, arguments: GenericArguments = None):
        super().__init__()

        if name_or_signature is None or isinstance(name_or_signature, str):
            self._signature = SignatureTemplate(name_or_signature)
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

        self._nested_definitions = NotifyingList()

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

        self._nested_definitions.append += on_add_member

        self._fields.pop += on_remove_member
        self._methods.pop += on_remove_member
        self._properties.pop += on_remove_member
        self._constructors.pop += on_remove_member

        self._nested_definitions.pop += on_remove_member

        self._fields.remove += on_remove_member
        self._methods.remove += on_remove_member
        self._properties.remove += on_remove_member
        self._constructors.remove += on_remove_member

        self._nested_definitions.remove += on_remove_member

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
    def signature(self, value: Signature | SignatureTemplate):
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
            if isinstance(field, FieldTemplate):
                result = field.construct(args)
            fields.append(result)

        methods = []
        for method in self.methods:
            result = method
            if isinstance(method, MethodTemplate):
                result = method.construct(args)
            methods.append(result)

        props = []
        for prop in self.properties:
            result = prop
            if isinstance(prop, PropertyTemplate):
                result = prop.construct(args)
            props.append(result)

        if any(
                isinstance(item, IConstructor) for item in [signature, *fields, *methods, *props]
        ):
            result = (generic_factory or ClassTemplate)(signature, constructor=self.constructor or self, arguments=args)
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


class ClassTemplate(OOPObjectTemplate, TypeProtocol):
    _base: "Class | GenericClass | ConstructedClass | None"

    _interfaces: list["GenericInterface | Interface"]

    _nested_definitions: NotifyingList["GenericNestedClass | GenericNestedInterface | NestedClass | NestedInterface"]

    def __init__(self, name_or_signature: str | Signature | SignatureTemplate, base: "Class | GenericClass | ConstructedClass | None" = None, constructor: "ClassTemplate" = None,
                 arguments: GenericArguments = None):
        super().__init__(name_or_signature, constructor, arguments)

        self._base = base

        self._interfaces = []

        self._nested_definitions = NotifyingList()

        self._nested_definitions.append += self.on_add_member
        self._nested_definitions.pop += self.on_remove_member
        self._nested_definitions.remove += self.on_remove_member

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
    def nested_definitions(self):
        return self._nested_definitions

    def assignable_to(self, target: TypeProtocol) -> bool:
        return target is self

    def assignable_from(self, source: TypeProtocol) -> bool:
        if source is self:
            return True

        if isinstance(source, ConstructedClass):
            return source.constructor is self

        return False

    def construct(
            self,
            args: dict[Parameter | ParameterTemplate, ObjectProtocol | Parameter | ParameterTemplate],
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
            if isinstance(interface, InterfaceTemplate):
                result = interface.construct(args)
            interfaces.append(result)

        if any(isinstance(item, IConstructor) for item in [base, *interfaces]):
            factory = ClassTemplate

        result = super().construct(args, factory or ConstructedClass, generic_factory or ClassTemplate, **kwargs)

        result.base = base

        for interface in interfaces:
            result.interfaces.append(interface)

        for nested_class_or_interface in self._nested_definitions:
            if isinstance(nested_class_or_interface, IConstructor):
                result.nested_definitions.append(nested_class_or_interface.construct(args, **kwargs))
            else:
                result.nested_definitions.append(nested_class_or_interface)

        return result

    def __repr__(self):
        return f"class {self.signature}"
        # declaration = \
        #     f"class{' ' if self.name else ''}{self.signature} " \
        #     f"{(f'< ' + ', '.join(base.name for base in [*((self._base,) if self._base is not None else ()), *self._interfaces]) + ' ') if self.base is not None or self._interfaces else ''}{{ "
        #
        # members = "".join(map(lambda m: "\n\t" + repr(m), self._member_list))
        #
        # if members:
        #     return declaration + members + "\n}"
        # return declaration + '}'


class InterfaceTemplate(OOPObjectTemplate):
    _bases: list["Interface | GenericInterface | ConstructedInterface"]

    def __init__(self, name_or_signature: str | Signature | SignatureTemplate, constructor: "ClassTemplate" = None):
        super().__init__(name_or_signature, constructor)

        self._bases = []

        self._nested_definitions = NotifyingList()

        self._nested_definitions.append += self.on_add_member
        self._nested_definitions.pop += self.on_remove_member
        self._nested_definitions.remove += self.on_remove_member

    @property
    def bases(self):
        return self._bases

    @property
    def nested_classes_and_interfaces(self):
        return self._nested_definitions

    def construct(
            self,
            args: dict[Parameter | ParameterTemplate, ObjectProtocol | Parameter | ParameterTemplate],
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
            factory = InterfaceTemplate

        result = super().construct(args, factory or ConstructedInterface, generic_factory or InterfaceTemplate, **kwargs)

        for base in bases:
            result.bases.append(base)

        for nested_definition in self._nested_definitions:
            if isinstance(nested_definition, IConstructor):
                result.nested_definitions.append(nested_definition.construct(args, **kwargs))
            else:
                result.nested_definitions.append(nested_definition)

        return result

    def __repr__(self):
        declaration = f"interface{' ' if self.name else ''}{self.signature} {(f'< ' + ', '.join(base.name for base in self._bases) + ' ') if self.bases else ''}{{"

        members = "".join(map(lambda m: "\n\t" + repr(m), self._member_list))

        if members:
            return declaration + members + "\n}"
        return declaration + '}'


class TypeclassTemplate(OOPObjectTemplate):
    _bases: list["Typeclass | ConstructedTypeclass | GenericTypeclass"]

    def __init__(self, name_or_signature: str | Signature | SignatureTemplate, constructor: "ClassTemplate" = None):
        super().__init__(name_or_signature, constructor)

        self._bases = []

    @property
    def bases(self):
        return self._bases

    def construct(
            self,
            args: dict[Parameter | ParameterTemplate, ObjectProtocol | Parameter | ParameterTemplate],
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
            factory = TypeclassTemplate

        result = super().construct(args, factory or ConstructedTypeclass, generic_factory or TypeclassTemplate, **kwargs)

        for base in bases:
            result.bases.append(base)

        return result

    def __repr__(self):
        declaration = f"typeclass{' ' if self.name else ''}{self.signature} {(f'< ' + ', '.join(base.name for base in self._bases) + ' ') if self.bases else ''}{{"

        members = "".join(map(lambda m: "\n\t" + repr(m), self._member_list))

        if members:
            return declaration + members + "\n}"
        return declaration + '}'


class IConstructedObject(Generic[_T]):
    origin: IConstructor[_T]


class ConstructedClass(Class, IConstructedObject[Class]):
    def __init__(self, name: str, constructor: ClassTemplate, arguments: dict[Parameter | ParameterTemplate, ObjectProtocol]):
        super().__init__(name)
        self.origin = constructor
        self.arguments = arguments


class ConstructedInterface(Interface, IConstructedObject[Interface]):
    def __init__(self, name: str, constructor: InterfaceTemplate, arguments: dict[Parameter | ParameterTemplate, TypeProtocol | Parameter | ParameterTemplate]):
        super().__init__(name)
        self.origin = constructor
        self.args = arguments


class ConstructedTypeclass(Typeclass, IConstructedObject[Typeclass]):
    def __init__(self, name: str, constructor: TypeclassTemplate):
        super().__init__(name)
        self.origin = constructor


if __name__ == '__main__':
    from miniz.type_system import Type, Boolean

    iiterable = InterfaceTemplate("IIterable")
    _T = Parameter("T", Type)
    iiterable.signature.positional_parameters.append(_T)

    iiterator = InterfaceTemplate("IIterator")
    _IteratorT = Parameter("T", Type)
    iiterator.signature.positional_parameters.append(_IteratorT)

    iiterable_get_iterator = MethodTemplate(None, "get_iterator", _T)
    # iiterable_get_iterator = GenericMethod(None, "get_iterator", iiterator.construct({_IteratorT: _T}))
    iiterable.methods.append(iiterable_get_iterator)

    print(iiterable)

    list_class_signature = SignatureTemplate("List")
    T = Parameter("T", Type)
    list_class_signature.positional_parameters.append(T)

    list_class = ClassTemplate(list_class_signature)

    list_class.interfaces.append(iiterable.construct({_T: T}))

    list_add = MethodTemplate(None, "add", Boolean)
    list_add.positional_parameters.append(ParameterTemplate("item", T))

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
