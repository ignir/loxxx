from functools import singledispatchmethod
from typing import Any, Iterable, List, Optional

from loxxx.expressions import Assign, Expression, Binary, Logical, Unary, Grouping, Literal, Variable
from loxxx.scanner import Token, TokenType
from loxxx.statements import Block, ExpressionStatement, If, PrintStatement, Statement, VariableDeclaration, While


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

    def get(self, name: Token) -> Any:
        if name.lexeme in self._values:
            return self._values[name.lexeme]
        if self._outer:
            return self._outer.get(name)

        raise LoxRuntimeError(name, f"Undefined variable {name.lexeme!r}.")


class Interpreter:
    def __init__(self) -> None:
        self._environment = Environment()

    def interpret(self, statements: Iterable[Statement]) -> None:
        from loxxx.lox import Lox

        try:
            for statement in statements:
                self.execute(statement)
        except LoxRuntimeError as error:
            Lox.runtime_error(error)

    def interpret_repl(self, statements: Iterable[Statement]) -> Any:
        from loxxx.lox import Lox

        if len(statements) == 1 and isinstance(statements[0], ExpressionStatement):
            try:
                print(self.evaluate(statements[0].expression))
            except LoxRuntimeError as error:
                Lox.runtime_error(error)
        else:
            self.interpret(statements)

    @singledispatchmethod
    def execute(self, statement: Statement) -> None:
        raise NotImplementedError

    @singledispatchmethod
    def evaluate(self, expression: Expression) -> Any:
        raise NotImplementedError

    @execute.register
    def _(self, statement: Block) -> None:
        self._execute_block(statement.statements, Environment(self._environment))

    def _execute_block(self, statements: List[Statement], environment: Environment) -> None:
        outer_environment = self._environment
        try:
            self._environment = environment
            for statement in statements:
                self.execute(statement)
        finally:
            self._environment = outer_environment

    @execute.register
    def _(self, statement: ExpressionStatement) -> None:
        self.evaluate(statement.expression)

    @execute.register
    def _(self, statement: If) -> None:
        if self._is_truthy(self.evaluate(statement.condition)):
            self.execute(statement.then_branch)
        elif statement.else_branch:
            self.execute(statement.else_branch)

    @execute.register
    def _(self, statement: PrintStatement) -> None:
        value = self.evaluate(statement.expression)
        print(self._stringify(value))

    @execute.register
    def _(self, statement: VariableDeclaration) -> None:
        value = statement.initializer and self.evaluate(statement.initializer)
        self._environment.define(statement.name.lexeme, value)

    @execute.register
    def _(self, statement: While) -> None:
        while self._is_truthy(self.evaluate(statement.condition)):
            self.execute(statement.body)

    @evaluate.register
    def _(self, expression: Literal) -> Any:
        return expression.value

    @evaluate.register
    def _(self, expression: Logical) -> Any:
        left = self.evaluate(expression.left)

        if expression.operator.type == TokenType.OR:
            if self._is_truthy(left):
                return left
        else:
            if not self._is_truthy(left):
                return left

        return self.evaluate(expression.right)

    @evaluate.register
    def _(self, expression: Grouping) -> Any:
        return self.evaluate(expression.expression)

    @evaluate.register
    def _(self, expression: Unary) -> Any:
        right = self.evaluate(expression.right)

        match expression.operator.type:
            case TokenType.BANG:
                return not self._is_truthy(right)
            case TokenType.MINUS:
                self._validate_number_operand(expression.operator, right)
                return -right

        raise Exception(f"No handler for a binary operator of type {expression.operator.type}")

    @evaluate.register
    def _(self, expression: Variable) -> Any:
        return self._environment.get(expression.name)

    @evaluate.register
    def _(self, expression: Assign) -> Any:
        value = self.evaluate(expression.value)
        self._environment.assign(expression.name, value)
        return value

    @evaluate.register
    def _(self, expression: Binary) -> Any:
        left = self.evaluate(expression.left)
        right = self.evaluate(expression.right)

        match expression.operator.type:
            case TokenType.EQUAL_EQUAL:
                return left == right
            case TokenType.BANG_EQUAL:
                return left != right
            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float) or isinstance(left, str) and isinstance(right, str):
                    return left + right  # type: ignore
                raise LoxRuntimeError(expression.operator, "Both operands must be either Numbers or Strings")
            case TokenType.MINUS:
                self._validate_number_operands(expression.operator, left, right)
                return left - right
            case TokenType.SLASH:
                self._validate_number_operands(expression.operator, left, right)
                if right == 0:
                    raise LoxRuntimeError(expression.operator, "Division by zero")
                return left / right
            case TokenType.STAR:
                self._validate_number_operands(expression.operator, left, right)
                return left * right
            case TokenType.GREATER:
                self._validate_number_operands(expression.operator, left, right)
                return left > right
            case TokenType.GREATER_EQUAL:
                self._validate_number_operands(expression.operator, left, right)
                return left >= right
            case TokenType.LESS:
                self._validate_number_operands(expression.operator, left, right)
                return left < right
            case TokenType.LESS_EQUAL:
                self._validate_number_operands(expression.operator, left, right)
                return left <= right

        raise Exception(f"No handler for a binary operator of type {expression.operator.type}")

    def _is_truthy(self, o: object) -> bool:
        if o is None:
            return False
        if isinstance(o, bool):
            return o
        return True

    def _validate_number_operand(self, operator: Token, operand: object) -> None:
        if not isinstance(operand, float):
            return
        raise LoxRuntimeError(operator, "Operand must be a number.")

    def _validate_number_operands(self, operator: Token, left_operand: object, right_operand: object) -> None:
        if isinstance(left_operand, float) and isinstance(right_operand, float):
            return
        raise LoxRuntimeError(operator, "Operands must be numbers.")

    def _stringify(self, value: object) -> str:
        if value is None:
            return "nil"

        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, float):
            if (s := str(value)).endswith(".0"):
                return s[:-2]
            return s
        return str(value)


class LoxRuntimeError(Exception):
    def __init__(self, token: Token, message: str):
        self.token = token
        self.message = message

    def __str__(self):
        return f"{self.token.lexeme}: {self.message}"
