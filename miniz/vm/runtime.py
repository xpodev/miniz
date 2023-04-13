from functools import singledispatchmethod

from miniz.function import Function
from miniz.generic.generic_construction import IConstructor
from miniz.signature import Parameter
from miniz.type_system import ObjectProtocol
from miniz.vm.instructions import Instruction, Return, Call, LoadArgument, LoadObject, EndOfProgram


class GenericInstructionExecuted(Exception):
    ...


class InvalidInstructionError(Exception):
    ...


class Code:
    _ip: int
    _instructions: list[Instruction]

    def __init__(self, instructions: list[Instruction]):
        self._instructions = instructions
        self._ip = 0

    @property
    def instruction(self):
        return self._instructions[self._ip]

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

    def __init__(self, function: Function, args: dict[Parameter, ObjectProtocol]):
        self._function = function
        self._args = args

        if not self._function.body.has_body:
            raise ValueError(f"Called an empty (declaration) function")

        super().__init__(self._function.body.instructions.copy())

    def argument(self, parameter: Parameter):
        return self._args[parameter]


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

    def pop(self) -> ObjectProtocol:
        return self._stack.pop()

    def next_instruction(self) -> Instruction:
        return self._frame.next_instruction()


class Interpreter:
    """
    The VM may only execute concrete instructions.

    This VM implementation assumes the input code was checked and validated.
    """
    _ctx: ExecutionContext
    _running: bool

    def __init__(self, code: Code | list[Instruction]):
        if isinstance(code, list):
            code = Code(code)
        self._ctx = ExecutionContext(code)
        self._running = False

    @property
    def ctx(self):
        return self._ctx

    def run(self):
        self._running = True
        while self._running:
            self.execute(self.ctx.next_instruction())

    def execute(self, inst: Instruction):
        # if not isinstance(inst, Instruction):
        #     raise TypeError(f"Expected an instruction, got \'{type(inst)}\'")
        # if isinstance(inst, IConstructor):
        #     raise TypeError(f"May not execute generic instructions, got \'{inst}\'")
        return self._execute(inst)

    @singledispatchmethod
    def _execute(self, inst: Instruction):
        raise NotImplementedError(f"Executing instruction of type \'{type(inst)}\' is not implemented yet")

    _exec = _execute.register

    @_exec
    def _(self, inst: Call):
        if inst.callee is None:
            inst.callee = self.ctx.pop()

        # if not isinstance(inst.callee, Function):
        #     raise InvalidInstructionError(f"`call` instruction may only be used with a Z# function, not \'{inst.callee}\'")

        args = {p: self.ctx.pop() for p in reversed(inst.callee.signature.parameters)}
        self.ctx.push_frame(inst.callee, args)

    @_exec
    def _(self, _: EndOfProgram):
        self._running = False

    @_exec
    def _(self, inst: LoadArgument):
        self.ctx.push(self.ctx.frame.argument(inst.parameter))

    @_exec
    def _(self, inst: LoadObject):
        self.ctx.push(inst.object)

    @_exec
    def _(self, inst: Return):
        if inst.has_return_value:
            return_value = self.ctx.pop()

            self.ctx.pop_frame()

            self.ctx.push(return_value)
        else:
            self.ctx.pop_frame()


if __name__ == '__main__':
    from miniz.type_system import Boolean

    f = Function(None, "f")

    f.positional_parameters.append(Parameter("x", Boolean))
    f.body.instructions.append(LoadArgument(f.positional_parameters[0]))
    f.body.instructions.append(Return(True))

    interpreter = Interpreter([LoadObject(Boolean.TrueInstance), Call(f), EndOfProgram()])
    interpreter.run()

    print(interpreter.ctx.pop())
