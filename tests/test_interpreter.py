from loxxx.scanner import Token, TokenType
from loxxx.expressions import Binary, Literal
from loxxx.interpreter import Interpeter, LoxRuntimeError

import pytest


def test_addition():
    interpreter = Interpeter()
    
    expression = Binary(Literal(float(10)), Token(TokenType.PLUS, "+", None, 1), Literal(float(1)))
    assert interpreter.evaluate(expression) == 11

    expression = Binary(Literal("ab"), Token(TokenType.PLUS, "+", None, 1), Literal("cd"))
    assert interpreter.evaluate(expression) == "abcd"    

    expression = Binary(Literal("10"), Token(TokenType.PLUS, "+", None, 1), Literal(float(1)))
    with pytest.raises(LoxRuntimeError) as error:
        interpreter.evaluate(expression)
        assert error.message == "Both operands must be either Numbers or Strings"
