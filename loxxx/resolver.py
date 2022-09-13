from dataclasses import dataclass
from enum import Enum, auto
from functools import singledispatchmethod

from loxxx.expressions import Assign, Binary, Call, Expression, FunctionDeclaration, Grouping, Literal, Logical, Unary, Variable
from loxxx.interpreter import Interpreter
from loxxx.scanner import Token
from loxxx.statements import Block, ExpressionStatement, If, PrintStatement, Return, Statement, VariableDeclaration, While


class FunctionType(Enum):
    NONE = auto()
    FUNCTION = auto()


class Resolver:
    def __init__(self, interpreter: Interpreter) -> None:
        self.errors = []
        self._current_function = FunctionType.NONE
        self._interpreter = interpreter
        self._scopes: list[dict[str, VariableInScope]] = []

    def run(self, statements: list[Statement]) -> None:
        self._begin_scope()
        self.resolve(statements)
        self._end_scope()

    def resolve(self, statements: list[Statement]) -> None:
        for statement in statements:
            self._resolve(statement)

    @singledispatchmethod
    def _resolve(self, statement: Statement | Expression) -> None:
        raise NotImplementedError

    @_resolve.register
    def _(self, statement: Block) -> None:
        self._begin_scope()
        self.resolve(statement.statements)
        self._end_scope()

    @_resolve.register
    def _(self, statement: ExpressionStatement) -> None:
        self._resolve(statement.expression)

    @_resolve.register
    def _(self, statement: If) -> None:
        self._resolve(statement.condition)
        self._resolve(statement.then_branch)
        if statement.else_branch:
            self._resolve(statement.else_branch)

    @_resolve.register
    def _(self, statement: PrintStatement) -> None:
        self._resolve(statement.expression)

    @_resolve.register
    def _(self, statement: Return) -> None:
        if self._current_function == FunctionType.NONE:
            self.errors.append((statement.keyword, "Can't return from top-level code."))

        if statement.expression:
            self._resolve(statement.expression)

    @_resolve.register
    def _(self, statement: VariableDeclaration) -> None:
        self._declare(statement.name)
        if statement.initializer:
            self._resolve(statement.initializer)
        self._define(statement.name)

    @_resolve.register
    def _(self, statement: While) -> None:
        self._resolve(statement.condition)
        self._resolve(statement.body)

    @_resolve.register
    def _(self, expression: Assign) -> None:
        self._resolve(expression.value)
        self._resolve_local(expression, expression.name)

    @_resolve.register
    def _(self, expression: Binary) -> None:
        self._resolve(expression.left)
        self._resolve(expression.right)

    @_resolve.register
    def _(self, expression: Call) -> None:
        self._resolve(expression.callee)
        for argument in expression.arguments:
            self._resolve(argument)

    @_resolve.register
    def _(self, expression: Grouping) -> None:
        self._resolve(expression.expression)

    @_resolve.register
    def _(self, expression: Literal) -> None:
        return

    @_resolve.register
    def _(self, expression: Logical) -> None:
        self._resolve(expression.left)
        self._resolve(expression.right)

    @_resolve.register
    def _(self, expression: Unary) -> None:
        self._resolve(expression.right)

    @_resolve.register
    def _(self, expression: Variable) -> None:
        lexeme = expression.name.lexeme
        if self._scopes:
            current_scope = self._scopes[-1]
            if lexeme in current_scope and not current_scope[lexeme].is_defined:
                self.errors.append((expression.name, "Can't read local variable in its own initializer."))
        self._resolve_local(expression, expression.name)

    @_resolve.register
    def _(self, expression: FunctionDeclaration) -> None:
        if expression.name:
            self._declare(expression.name)
            self._define(expression.name)
        self._resolve_function(expression, FunctionType.FUNCTION)

    def _resolve_function(self, expression: FunctionDeclaration, type: FunctionType) -> None:
        enclosing_function = self._current_function
        self._current_function = type

        self._begin_scope()
        for param in expression.params:
            self._declare(param)
            self._define(param)
        self.resolve(expression.body)
        self._end_scope()

        self._current_function = enclosing_function

    def _resolve_local(self, expression: Expression, name: Token) -> None:
        for distance, scope in enumerate(reversed(self._scopes)):
            if name.lexeme in scope:
                self._interpreter.resolve(expression, distance)
                scope[name.lexeme].has_references = True
                # TODO: Shouldn't we break the loop here?

    def _begin_scope(self) -> None:
        self._scopes.append({})

    def _end_scope(self) -> None:
        scope = self._scopes.pop()
        for lexeme, var in scope.items():
            if not var.has_references:
                self.errors.append((var.token, "A variable is never used"))

    def _declare(self, name: Token) -> None:
        if not self._scopes:
            return
        scope = self._scopes[-1]
        if name.lexeme in scope:
            self.errors.append((name, "A variable with this name is already defined in this scope."))
        scope[name.lexeme] = VariableInScope(name)

    def _define(self, name: Token) -> None:
        if not self._scopes:
            return
        self._scopes[-1][name.lexeme].is_defined = True


@dataclass
class VariableInScope:
    token: Token
    is_defined: bool = False
    has_references: bool = False
