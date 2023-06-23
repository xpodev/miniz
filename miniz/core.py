class ObjectProtocol:
    runtime_type: "TypeProtocol"

    def is_instance_of(self, __type: "TypeProtocol") -> bool:
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


ImplementsType = TypeProtocol
