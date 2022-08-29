from typing import Optional, Any

from loxxx.errors import LoxRuntimeError
from loxxx.scanner import Token


class Environment:
    def __init__(self, outer: Optional['Environment'] = None):
        self._outer = outer
        self._values: dict = {}

    def define(self, name: str, value: Any) -> None:
        self._values[name] = value

    def assign(self, name: Token, value: Any) -> None:
        if name.lexeme in self._values:
            self._values[name.lexeme] = value
            return
        if self._outer:
            return self._outer.assign(name, value)

        raise LoxRuntimeError(name, f"Undefined variable {name.lexeme!r}.")

    def assign_at(self, distance: int, name: Token, value: Any) -> None:
        self._find_ancestor(distance)._values[name.lexeme] = value

    def get(self, name: Token) -> Any:
        if name.lexeme in self._values:
            return self._values[name.lexeme]
        if self._outer:
            return self._outer.get(name)

        raise LoxRuntimeError(name, f"Undefined variable {name.lexeme!r}.")

    def get_at(self, distance: int, name: str) -> Any:
        return self._find_ancestor(distance)._values[name]

    def _find_ancestor(self, distance: int) -> 'Environment':
        environment = self
        for _ in range(distance):
            environment = environment._outer
        return environment
