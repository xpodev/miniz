from miniz.core import ObjectProtocol


class IMiniZObject(ObjectProtocol):
    ...


class INamed(IMiniZObject):
    name: str | None


class ScopeProtocol:
    """
    Represents a scope
    """

    def get_name(self, name: str) -> ObjectProtocol:
        """
        Returns the value associated with the given `name` in this scope.

        :raises NameNotFoundError: if the given name could not be found.
        """
