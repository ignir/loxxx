from dataclasses import dataclass
from typing import List

from loxxx.expressions.expressions import FunctionDeclaration
from loxxx.expressions.base import Expression
from loxxx.scanner import Token
from loxxx.statements.base import Statement


@dataclass(frozen=True)
class Class(Statement):
    name: Token
    methods: List[FunctionDeclaration]
    static_methods: List[FunctionDeclaration]


@dataclass(frozen=True)
class ExpressionStatement(Statement):
    expression: Expression


@dataclass(frozen=True)
class If(Statement):
    condition: Expression
    then_branch: Statement
    else_branch: Statement


@dataclass(frozen=True)
class PrintStatement(Statement):
    expression: Expression


@dataclass(frozen=True)
class Return(Statement):
    keyword: Token
    expression: Expression | None


@dataclass(frozen=True)
class VariableDeclaration(Statement):
    name: Token
    initializer: Expression | None


@dataclass(frozen=True)
class While(Statement):
    condition: Expression
    body: Statement


@dataclass(frozen=True)
class Block(Statement):
    statements: List[Statement]
