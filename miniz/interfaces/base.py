from miniz.core import ObjectProtocol


class IMiniZObject(ObjectProtocol):
    ...


class INamed(IMiniZObject):
    name: str | None
