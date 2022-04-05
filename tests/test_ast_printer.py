from loxxx.ast_printer import ASTPrinter, RPNPrinter
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


def test_rpn_printer():
    expr = Binary(
        Unary(
            Token(TokenType.MINUS, "-", None, 1),
            Literal(123),
        ),
        Token(TokenType.STAR, "*", None, 1),
        Grouping(Literal(45.67)),
    )

    assert RPNPrinter().to_str(expr) == "123 - 45.67 *"

    expr = Binary(
        Grouping(Binary(
            Literal(1),
            Token(TokenType.PLUS, "+", None, 1),
            Literal(2),
        )),
        Token(TokenType.STAR, "*", None, 1),
        Grouping(Binary(
            Literal(4),
            Token(TokenType.MINUS, "-", None, 1),
            Literal(3),
        )),
    )

    assert RPNPrinter().to_str(expr) == "1 2 + 4 3 - *"
