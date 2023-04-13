"""
This module contains objects that are only used by the CT interpreter.

Objects in this module may be exposed to the Z# environment via the `ct-interpreter` module.
"""
from contextlib import contextmanager

from miniz.function import Function
from miniz.scope import Scope


class Frame(Scope):
    function: Function

    def __init__(self, function: Function):
        super().__init__(function.lexical_scope)
        self.function = function


class ExecutionContext:
    """
    An execution context of a single thread.
    """

    _current_scope: Scope
    _current_frame: Frame | None

    def __init__(self, global_scope: Scope = Scope()):
        self._current_scope = global_scope
        self._current_frame = None

    @property
    def current_frame(self):
        return self._current_frame

    @property
    def current_scope(self):
        return self._current_scope

    @contextmanager
    def frame(self, function: Function):
        old, self._current_frame = self._current_frame, Frame(function)
        self._current_scope = self._current_frame
        try:
            yield old, self._current_frame
        finally:
            self._current_frame = old

    @contextmanager
    def scope(self, scope: Scope = None, parent: bool | Scope = None):
        if parent is True:
            parent = self._current_scope
        elif parent is False:
            parent = None
        else:
            assert isinstance(parent, Scope)
        if scope is None:
            scope = Scope(parent)
        old, self._current_scope = self._current_scope, scope
        try:
            yield scope
        finally:
            self._current_scope = old
