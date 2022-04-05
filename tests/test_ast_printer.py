from loxxx.ast_printer import ASTPrinter
from loxxx.expressions import Binary, Unary, Literal, Grouping
from loxxx.scanner import Token, TokenType


def test_ast_printer():
    expr = Binary(
        Unary(
            Token(TokenType.MINUS, "-", None, 1),
            Literal(123),
        ),
        Token(TokenType.STAR, "*", None, 1),
        Grouping(Literal(45.67)),
    )

    assert ASTPrinter().to_str(expr) == "(* (- 123) (group 45.67))"