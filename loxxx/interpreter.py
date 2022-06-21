from functools import singledispatchmethod

from loxxx.expressions import Expression, Binary, Unary, Grouping, Literal
from loxxx.scanner import Token, TokenType


class Interpeter:
    def intepret(self, expression: Expression) -> None:
        from loxxx.lox import Lox
        
        try:
            value = self.evaluate(expression)
            print(self._stringify(value))
        except LoxRuntimeError as error:
            Lox.runtime_error(error)
   
    @singledispatchmethod
    def evaluate(self, expression: Expression) -> object:
        raise NotImplementedError

    @evaluate.register
    def _(self, expression: Literal) -> object:
        return expression.value

    @evaluate.register
    def _(self, expression: Grouping) -> object:
        return self.evaluate(expression.expression)

    @evaluate.register
    def _(self, expression: Unary) -> object:
        right = self.evaluate(expression.right)

        match expression.operator.type:
            case TokenType.BANG:
                return not self._is_truthy(right)
            case TokenType.MINUS:
                self._validate_number_operand(expression.operator, right)
                return -right

    @evaluate.register
    def _(self, expression: Binary) -> object:
        left = self.evaluate(expression.left)
        right = self.evaluate(expression.right)

        match expression.operator.type:
            case TokenType.EQUAL:
                return left == right
            case TokenType.BANG_EQUAL:
                return left != right
            case TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float) or isinstance(left, str) and isinstance(right, str):
                    return left + right
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
        
        s = str(value)
        if isinstance(value, float) and s.endswith(".0"):
            return s[:-2]
        return s


class LoxRuntimeError(Exception):
    def __init__(self, token: Token, message: str):
        self.token = token
        self.message = message

    def __str__(self):
        return f"{self.token.lexeme}: {self.message}"