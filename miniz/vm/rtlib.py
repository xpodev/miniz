from typing import Type, TypeVar

from miniz.concrete.function import Function, Local
from miniz.concrete.oop import Class, Binding
from miniz.concrete.signature import Parameter
from miniz.type_system import ObjectProtocol
from miniz.vm.instruction import Instruction
from utils import SingletonMeta

_T = TypeVar("_T", bound=ObjectProtocol)


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


class Code:
    _ip: int
    _instructions: list[Instruction]

    def __init__(self, instructions: list[Instruction]):
        self._instructions = instructions
        self._ip = 0

    @property
    def instruction(self):
        return self._instructions[self._ip]

    @property
    def instructions(self):
        return self._instructions

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

    def __init__(self, code: Code):
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

    def pop(self, _: Type[_T] = ObjectProtocol) -> _T:
        return self._stack.pop()

    def next_instruction(self) -> Instruction:
        return self._frame.next_instruction()
