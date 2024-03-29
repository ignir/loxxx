from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from loxxx.environment import Environment

if TYPE_CHECKING:
    from loxxx.interpreter import Interpreter
    from loxxx.expressions import FunctionDeclaration


class Callable(ABC):
    @abstractmethod
    def call(self, interpreter: 'Interpreter', arguments: list[Any]) -> Any:
        pass

    @property
    @abstractmethod
    def arity(self) -> int:
        pass


class Function(Callable):
    def __init__(self, declaration: 'FunctionDeclaration', closure: Environment) -> None:
        self._declaration = declaration
        self._closure = closure

    def call(self, interpreter: 'Interpreter', arguments: list[Any]) -> Any:
        environment = Environment(self._closure)
        for param, argument in zip(self._declaration.params, arguments):
            environment.define(param.lexeme, argument)

        try:
            interpreter.execute_block(self._declaration.body, environment)
        except FunctionReturn as ret:
            return ret.value
        return None

    @property
    def arity(self) -> int:
        return len(self._declaration.params)

    def __str__(self) -> str:
        if self._declaration.name:
            return f"<fn {self._declaration.name.lexeme}>"
        return "<anonymous fn>"


class FunctionReturn(Exception):
    def __init__(self, value: Any):
        self.value = value
