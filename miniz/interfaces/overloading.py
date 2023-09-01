from typing import Generic, TypeVar

from miniz.core import TypeProtocol
from miniz.generic import GenericParameter
from miniz.vm.instruction import Instruction

from typeclass import Typeclass, typeclass_api

_T = TypeVar("_T", bound="IOverloaded")


class Argument:
    code: list[Instruction]
    type: TypeProtocol


class OverloadMatchResult(Generic[_T]):
    matched_args: list[Argument] | None
    matched_kwargs: dict[str, Argument] | None

    unmatched_args: list[Argument] | None
    unmatched_kwargs: dict[str, Argument] | None

    callee: _T | None
    callee_instructions: list[Instruction] | None
    call_instruction: Instruction

    @property
    def is_partial_match(self):
        return self.unmatched_args or self.unmatched_kwargs

    @property
    def is_full_match(self):
        return not self.is_partial_match

    @property
    def has_callee(self):
        return self.callee is not None

    @property
    def has_args(self):
        return bool(self.matched_args)

    @property
    def has_kwargs(self):
        return bool(self.matched_kwargs)


class IOverloaded(Typeclass):
    @typeclass_api
    def match(self, args: list[Argument], kwargs: list[tuple[str, Argument]], *, strict: bool = False, type_mappings: dict[GenericParameter, TypeProtocol] = None) -> OverloadMatchResult | None:
        raise NotImplementedError
