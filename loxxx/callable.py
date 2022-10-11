from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

from loxxx.environment import Environment
from loxxx.errors import LoxRuntimeError
from loxxx.scanner import Token

if TYPE_CHECKING:
    from loxxx.interpreter import Interpreter
    from loxxx.expressions.expressions import FunctionDeclaration


class Callable(ABC):
    @abstractmethod
    def call(self, interpreter: 'Interpreter', arguments: list[Any]) -> Any:
        pass

    @property
    @abstractmethod
    def arity(self) -> int:
        pass


class Function(Callable):
    def __init__(self, declaration: 'FunctionDeclaration', closure: Environment, is_initializer: bool) -> None:
        self._declaration = declaration
        self._closure = closure
        self._is_initializer = is_initializer

    def bind(self, class_instance: 'Instance') -> 'Function':
        environment = Environment(self._closure)
        environment.define("this", class_instance)
        return Function(self._declaration, environment, self._is_initializer)

    def call(self, interpreter: 'Interpreter', arguments: list[Any]) -> Any:
        environment = Environment(self._closure)
        for param, argument in zip(self._declaration.params, arguments):
            environment.define(param.lexeme, argument)

        try:
            interpreter.execute_block(self._declaration.body, environment)
        except FunctionReturn as ret:
            if self._is_initializer:
                return self._closure.get_at(0, "this")
            return ret.value

        if self._is_initializer:
            return self._closure.get_at(0, "this")

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


class Class(Callable):
    def __init__(self, name: str, methods: Dict[str, Function]) -> None:
        self.name = name
        self.methods = methods

    def call(self, interpreter: 'Interpreter', arguments: list[Any]) -> Any:
        instance = Instance(self)
        if initializer := self.find_method("init"):
            initializer.bind(instance).call(interpreter, arguments)
        return instance

    def find_method(self, name: str) -> Optional[Function]:
        return self.methods.get(name)

    @property
    def arity(self) -> int:
        if initializer := self.find_method("init"):
            return initializer.arity
        return 0

    def __str__(self):
        return self.name


class Instance:
    def __init__(self, klass: Class) -> None:
        self._class = klass
        self._fields = {}

    def get(self, name: Token) -> Any:
        if name.lexeme in self._fields:
            return self._fields[name.lexeme]

        method = self._class.find_method(name.lexeme)
        if method:
            return method.bind(self)

        raise LoxRuntimeError(name, f"Undefined property '{name.lexeme}'.")

    def set(self, name: Token, value: Any) -> None:
        self._fields[name.lexeme] = value

    def __str__(self):
        return f"{self._class.name} instance"
