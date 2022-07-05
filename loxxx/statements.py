from dataclasses import dataclass
from typing import List

from loxxx.expressions import Expression
from loxxx.scanner import Token


class Statement:
    pass


@dataclass
class ExpressionStatement(Statement):
    expression: Expression


@dataclass
class PrintStatement(Statement):
    expression: Expression


@dataclass
class VariableDeclaration(Statement):
    name: Token
    initializer: Expression | None


@dataclass
class Block(Statement):
    statements: List[Statement]
