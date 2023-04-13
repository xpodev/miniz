from miniz.type_system import ObjectProtocol


class Scope:
    """
    Represents a scope. A scope is a collection of `name: value` pairs.

    Scopes are parented to form a tree. Name lookup starts at the current scope and up the hierarchy
    until there is no parent scope.
    """

    parent: "Scope | None"

    def __init__(self, parent: "Scope | None" = None):
        self.parent = parent

    def find(self, name: str, instance: ObjectProtocol) -> ObjectProtocol | None:
        raise NotImplementedError
