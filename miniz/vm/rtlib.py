from typing import Type, TypeVar

from miniz.concrete.function import Function, Local
from miniz.concrete.oop import Class, Binding
from miniz.concrete.signature import Parameter
from miniz.interfaces.execution import IExecutable, ITarget
from miniz.type_system import ObjectProtocol
from miniz.vm.instruction import Instruction
from utils import SingletonMeta, NotifyingList

_T = TypeVar("_T", bound=ObjectProtocol)


_SENTINEL = object()


class EndOfProgram(Instruction, metaclass=SingletonMeta):
    ...


class GenericInstructionExecuted(Exception):
    ...


class InvalidInstructionError(Exception):
    ...


class Instance(ObjectProtocol):
    _data: list[ObjectProtocol | None]

    def __init__(self, runtime_type: Class):
        self.runtime_type = runtime_type
        self._data = [None for field in runtime_type.fields if field.binding == Binding.Instance]

    @property
    def data(self):
        return self._data


class CodeLocal(ITarget["Code"]):
    ...


class Code(IExecutable):
    _ip: int
    _instructions: list[Instruction]
    _locals_impl: NotifyingList[CodeLocal]

    def __init__(self, instructions: list[Instruction]):
        self._instructions = instructions
        self._ip = 0
        self._locals_impl = NotifyingList()

        def on_add_local(_, local: ITarget):
            if not isinstance(local, CodeLocal):
                raise TypeError(f"Can only add \'{CodeLocal.__name__}\' objects to a \'{Code.__name__}\' object, not \'{type(local).__name__}\'")
            if local.is_member:
                raise ValueError(f"Local \'{local}\' is already owned by \'{local.owner}\'")
            local.owner = self

        def on_remove_local(_, local: ITarget | int):
            if isinstance(local, int):
                local = self._locals_impl[local]
            if local.owner is not self:
                raise ValueError(f"Local \'{local}\' is not owned by \'{self}\'")
            local.owner = None

        self._locals_impl.append += on_add_local
        self._locals_impl.remove += on_remove_local
        self._locals_impl.pop += on_remove_local

    @property
    def instruction(self):
        return self._instructions[self._ip]

    @property
    def instructions(self):
        return self._instructions

    @property
    def locals(self):
        return self._locals_impl

    def next_instruction(self) -> Instruction:
        inst = self.instruction
        self._ip += 1
        return inst

    def jump(self, target: Instruction | int):
        if isinstance(target, Instruction):
            target = target.index
        self._ip = target


class Frame(Code):
    _function: Function
    _args: dict[Parameter, ObjectProtocol]
    _locals: dict[Local, ObjectProtocol]

    def __init__(self, function: Function, args: dict[Parameter, ObjectProtocol]):
        self._function = function
        self._args = args
        self._locals = {
            local: None for local in function.locals
        }

        # if not self._function.body.has_body:
        #     raise ValueError(f"Called an empty (declaration) function")

        super().__init__(self._function.body.instructions.copy())

    @property
    def function(self):
        return self._function

    def argument(self, parameter: Parameter, value: ObjectProtocol | None = None) -> ObjectProtocol | None:
        if value is None:
            return self._args[parameter]
        self._args[parameter] = value

    def local(self, local: Local, value: ObjectProtocol | None = None) -> ObjectProtocol | None:
        if value is None:
            return self._locals[local]
        self._locals[local] = value


class ExecutionContext:
    """
    Execution context for a single thread.
    """

    _frame: Code | Frame
    _frames: list[Code]
    _stack: list[ObjectProtocol]

    def __init__(self, code: Code | None):
        self._frames = [code]
        self._frame = code
        self._stack = []

    @property
    def frame(self):
        return self._frame

    def push_frame(self, function: Function, args: dict[Parameter, ObjectProtocol] | list[ObjectProtocol]):
        if isinstance(args, list):
            args = {
                parameter: arg for parameter, arg in zip(function.signature.parameters, args)
            }
        self._frame = Frame(function, args)
        self._frames.append(self._frame)

    def pop_frame(self):
        self._frames.pop()
        self._frame = self._frames[-1]

    def push(self, value: ObjectProtocol):
        self._stack.append(value)

    def top(self, _: Type[_T] = ObjectProtocol) -> _T:
        return self._stack[-1]

    def pop(self, *, default: _T = _SENTINEL) -> _T:
        try:
            return self._stack.pop()
        except IndexError:
            if default is _SENTINEL:
                raise
            return default

    def next_instruction(self) -> Instruction:
        return self._frame.next_instruction()
