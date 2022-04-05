from functools import singledispatchmethod

from loxxx.expressions import Expression, Binary, Unary, Grouping, Literal


class ASTPrinter:
    @singledispatchmethod
    def to_str(self, expression: Expression) -> str:
        raise NotImplementedError

    @to_str.register
    def _(self, expression: Binary) -> str:
        return self.parenthesize(expression.operator.lexeme, expression.left, expression.right)

    @to_str.register
    def _(self, expression: Grouping) -> str:
        return self.parenthesize("group", expression.expression)        

    @to_str.register
    def _(self, expression: Literal) -> str:
        if expression.value is None:
            return "nil"
        return str(expression.value)

    @to_str.register
    def _(self, expression: Unary) -> str:
        return self.parenthesize(expression.operator.lexeme, expression.right)

    def parenthesize(self, name: str, *expressions: Expression) -> str:
        return f"({name} {' '.join(map(self.to_str, expressions))})"


class RPNPrinter:
    @singledispatchmethod
    def to_str(self, expression: Expression) -> str:
        raise NotImplementedError

    @to_str.register
    def _(self, expression: Binary) -> str:
        return " ".join([self.to_str(expression.left), self.to_str(expression.right), expression.operator.lexeme])

    @to_str.register
    def _(self, expression: Grouping) -> str:
        return self.to_str(expression.expression)

    @to_str.register
    def _(self, expression: Literal) -> str:
        if expression.value is None:
            return "nil"
        return str(expression.value)

    @to_str.register
    def _(self, expression: Unary) -> str:
        return " ".join([self.to_str(expression.right), expression.operator.lexeme]) 
