from functools import singledispatchmethod

from miniz.concrete.function import Function
from miniz.concrete.oop import Binding
from miniz.concrete.signature import Parameter
from miniz.type_system import Void
from miniz.vm.instructions import Instruction, Return, Call, LoadArgument, LoadObject, SetArgument, SetField, LoadField, LoadLocal, SetLocal, Jump, JumpIfFalse, JumpIfTrue, DuplicateTop, NoOperation, \
    TypeOf
from miniz.vm.rtlib import ExecutionContext, Code, EndOfProgram


class Interpreter:
    """
    The VM may only execute concrete instructions.

    This VM implementation assumes the input code was checked and validated.
    """
    _ctx: ExecutionContext | None
    _running: bool

    def __init__(self):
        self._ctx = None
        self._running = False

    @property
    def ctx(self):
        return self._ctx

    def run(self, code: Code | list[Instruction]):
        if isinstance(code, list):
            code = Code(code)
        if code.instructions[-1] is not EndOfProgram():
            code.instructions.append(EndOfProgram())
        self._ctx = ExecutionContext(code)
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
    def _(self, _: DuplicateTop):
        self.ctx.push(self.ctx.top())

    @_exec
    def _(self, _: EndOfProgram):
        self._running = False

    @_exec
    def _(self, inst: Jump):
        self.ctx.frame.jump(inst.target)

    @_exec
    def _(self, inst: JumpIfFalse):
        if self.ctx.pop() is Boolean.FalseInstance:
            self.ctx.frame.jump(inst.target)

    @_exec
    def _(self, inst: JumpIfTrue):
        if self.ctx.pop() is Boolean.TrueInstance:
            self.ctx.frame.jump(inst.target)

    @_exec
    def _(self, inst: LoadArgument):
        self.ctx.push(self.ctx.frame.argument(inst.parameter))

    @_exec
    def _(self, inst: LoadField):
        match inst.field.binding:
            case Binding.Instance:
                self.ctx.push(self.ctx.pop().data[inst.field.index])
            case Binding.Class:
                raise NotImplementedError
            case Binding.Static:
                raise NotImplementedError

    @_exec
    def _(self, inst: LoadLocal):
        self.ctx.push(self.ctx.frame.local(inst.local))

    @_exec
    def _(self, inst: LoadObject):
        self.ctx.push(inst.object)

    @_exec
    def _(self, _: NoOperation):
        ...

    @_exec
    def _(self, _: Return):
        if self.ctx.frame.function.return_type != Void:
            return_value = self.ctx.pop()

            self.ctx.pop_frame()

            self.ctx.push(return_value)
        else:
            self.ctx.pop_frame()

    @_exec
    def _(self, inst: SetArgument):
        self.ctx.frame.argument(inst.parameter, self.ctx.pop())

    @_exec
    def _(self, inst: SetField):
        value = self.ctx.pop()

        match inst.field.binding:
            case Binding.Instance:
                self.ctx.pop().data[inst.field.index] = value
            case Binding.Class:
                raise NotImplementedError
            case Binding.Static:
                raise NotImplementedError

    @_exec
    def _(self, inst: SetLocal):
        self.ctx.frame.local(inst.local, self.ctx.pop())

    @_exec
    def _(self, _: TypeOf):
        self.ctx.push(self.ctx.pop().runtime_type)


if __name__ == '__main__':
    from miniz.type_system import Boolean

    f = Function("f")

    f.positional_parameters.append(Parameter("x", Boolean))
    f.body.instructions.append(LoadArgument(f.positional_parameters[0]))
    f.body.instructions.append(Return())

    interpreter = Interpreter()
    interpreter.run([LoadObject(Boolean.TrueInstance), Call(f)])

    print(interpreter.ctx.pop())
