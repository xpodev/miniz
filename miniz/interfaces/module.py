from miniz.core import ImplementsType, ObjectProtocol
from miniz.interfaces.base import INamed
from miniz.interfaces.function import IFunction
from miniz.interfaces.oop import IClass, IInterface, ITypeclass, IStructure
from miniz.ownership import Owned


class IGlobal(Owned["IModuleBase"], INamed):
    type: ImplementsType
    default_value: ObjectProtocol | None


class IModuleBase(Owned["IModuleBase"], INamed):
    functions: list[IFunction]
    types: list[IClass | IInterface | ITypeclass | IStructure]
    submodules: list["IModule"]
    apis: list["IModuleAPI"]
    globals: list[IGlobal]

    specifications: list["IModuleAPI"]

    @property
    def items(self):
        return [
            *self.functions,
            *self.types,
            *self.submodules,
            *self.globals
        ]


class IModule(IModuleBase):
    entry_point: IFunction | None
    submodules: list["IModule"]
    module_apis: list["IModuleAPI"]


class IModuleAPI(IModuleBase):
    """
    Represents a module API.
    """

    implementations: list[IModule]
