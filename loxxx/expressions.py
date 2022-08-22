from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from loxxx.scanner import Token


class Expression:
    pass


@dataclass
class Binary(Expression):
    left: Expression
    operator: Token
    right: Expression


@dataclass
class Call(Expression):
    callee: Expression
    paren: Token
    arguments: list[Expression]


@dataclass
class Logical(Expression):
    left: Expression
    operator: Token
    right: Expression


@dataclass
class Unary(Expression):
    operator: Token
    right: Expression


@dataclass
class Grouping(Expression):
    expression: Expression


@dataclass
class Literal(Expression):
    value: float | str | bool | None


@dataclass
class Variable(Expression):
    name: Token


@dataclass
class Assign(Expression):
    name: Token
    value: Expression


from loxxx.statements import Statement

@dataclass
class FunctionDeclaration(Expression):
    name: Token | None
    params: List[Token]
    body: List[Statement]
