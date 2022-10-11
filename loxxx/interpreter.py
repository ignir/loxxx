from functools import singledispatchmethod
from typing import Any, Iterable, List

from loxxx.callable import Callable, Function, FunctionReturn, Class as LoxClass, Instance
from loxxx.environment import Environment
from loxxx.errors import LoxRuntimeError
from loxxx.expressions.expressions import (
    Assign,
    Expression,
    Binary,
    Call,
    FunctionDeclaration,
    Get,
    Grouping,
    Literal,
    Logical,
    Set,
    This,
    Unary,
    Variable,
)
from loxxx.native import clock
from loxxx.scanner import Token, TokenType
from loxxx.statements.statements import Block, Class, ExpressionStatement, If, PrintStatement, Return, Statement, VariableDeclaration, While


class Interpreter:
    def __init__(self) -> None:
        self.environment = self.globals = Environment()
        self.locals: dict[Expression, int] = {}

        self.globals.define("clock", clock())

    def interpret(self, statements: Iterable[Statement]) -> None:
        for statement in statements:
            self.execute(statement)

    def interpret_repl(self, statements: Iterable[Statement]) -> Any:
        if len(statements) == 1 and isinstance(statements[0], ExpressionStatement):
            print(self.evaluate(statements[0].expression))
        else:
            self.interpret(statements)

    @singledispatchmethod
    def execute(self, statement: Statement) -> None:
        raise NotImplementedError

    @singledispatchmethod
    def evaluate(self, expression: Expression) -> Any:
        raise NotImplementedError

    def resolve(self, expression: Expression, depth: int) -> None:
        self.locals[expression] = depth

    @execute.register
    def _(self, statement: Block) -> None:
        self.execute_block(statement.statements, Environment(self.environment))

    def execute_block(self, statements: List[Statement], environment: Environment) -> None:
        outer_environment = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = outer_environment

    @execute.register
    def _(self, statement: Class) -> None:
        self.environment.define(statement.name.lexeme, None)
        methods = {
            method.name.lexeme: Function(method, self.environment, method.name.lexeme == "init")
            for method in statement.methods
        }
        self.environment.assign(statement.name, LoxClass(statement.name.lexeme, methods))

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
    def _(self, statement: Return) -> None:
        value = None
        if statement.expression is not None:
            value = self.evaluate(statement.expression)
        raise FunctionReturn(value)

    @execute.register
    def _(self, statement: VariableDeclaration) -> None:
        value = statement.initializer and self.evaluate(statement.initializer)
        self.environment.define(statement.name.lexeme, value)

    @execute.register
    def _(self, statement: While) -> None:
        while self._is_truthy(self.evaluate(statement.condition)):
            self.execute(statement.body)

    @evaluate.register
    def _(self, expression: Call) -> Any:
        callee = self.evaluate(expression.callee)
        if not isinstance(callee, Callable):
            raise LoxRuntimeError(expression.paren, "Can only call functions and classes.")
        if len(expression.arguments) != callee.arity:
            raise LoxRuntimeError(expression.paren, f"Expected {callee.arity} arguments but got {len(expression.arguments)}.")

        arguments = [self.evaluate(argument) for argument in expression.arguments]
        return callee.call(self, arguments)

    @evaluate.register
    def _(self, expression: Get) -> Any:
        object = self.evaluate(expression.object)
        if not isinstance(object, Instance):
            raise LoxRuntimeError(expression.name, "Only instances have properties.")
        return object.get(expression.name)

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
    def _(self, expression: Set) -> Any:
        object = self.evaluate(expression.object)
        if not isinstance(object, Instance):
            raise LoxRuntimeError(expression.name, "Only instances have properties.")
        value = self.evaluate(expression.value)
        object.set(expression.name, value)
        return value

    @evaluate.register
    def _(self, expression: This) -> Any:
        return self._look_up_variable(expression.keyword, expression)

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
        return self._look_up_variable(expression.name, expression)

    @evaluate.register
    def _(self, expression: Assign) -> Any:
        value = self.evaluate(expression.value)

        distance = self.locals.get(expression)
        if distance is not None:
            self.environment.assign_at(distance, expression.name, value)
        else:
            self.globals.assign(expression.name, value)

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

    @evaluate.register
    def _(self, expression: FunctionDeclaration) -> Any:
        function = Function(expression, self.environment, False)
        if expression.name:
            self.environment.define(expression.name.lexeme, function)
        return function

    def _look_up_variable(self, name: Token, expression: Expression) -> Any:
        distance = self.locals.get(expression)
        if distance is not None:
            return self.environment.get_at(distance, name.lexeme)
        return self.globals.get(name)

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
