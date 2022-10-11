from dataclasses import dataclass
from typing import List

from loxxx.scanner import Token
from loxxx.statements.base import Statement
from .base import Expression


@dataclass(frozen=True)
class Binary(Expression):
    left: Expression
    operator: Token
    right: Expression


@dataclass(frozen=True)
class Call(Expression):
    callee: Expression
    paren: Token
    arguments: list[Expression]


@dataclass(frozen=True)
class Get(Expression):
    object: Expression
    name: Token


@dataclass(frozen=True)
class Logical(Expression):
    left: Expression
    operator: Token
    right: Expression


@dataclass(frozen=True)
class Set(Expression):
    object: Expression
    name: Token
    value: Expression


@dataclass(frozen=True)
class This(Expression):
    keyword: Token


@dataclass(frozen=True)
class Unary(Expression):
    operator: Token
    right: Expression


@dataclass(frozen=True)
class Grouping(Expression):
    expression: Expression


@dataclass(frozen=True)
class Literal(Expression):
    value: float | str | bool | None


@dataclass(frozen=True)
class Variable(Expression):
    name: Token


@dataclass(frozen=True)
class Assign(Expression):
    name: Token
    value: Expression


@dataclass(frozen=True)
class FunctionDeclaration(Expression):
    name: Token | None
    params: List[Token]
    body: List[Statement]
