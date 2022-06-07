from typing import List, Optional

from loxxx.expressions import Binary, Expression, Grouping, Literal, Unary
from loxxx.scanner import Token, TokenType


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._current = 0

    def parse(self) -> Optional[Expression]:
        try:
            return self.parse_expression()
        except ParseError:
            return None

    def parse_expression(self) -> Expression:
        return self.parse_equality()

    def parse_equality(self) -> Expression:
        expr = self.parse_comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = self.previous_token
            right = self.parse_comparison()
            expr = Binary(expr, operator, right)

        return expr

    def parse_comparison(self) -> Expression:
        expr = self.parse_term()

        while self.match(TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self.previous_token
            right = self.parse_term()
            expr = Binary(expr, operator, right)

        return expr

    def parse_term(self) -> Expression:
        expr = self.parse_factor()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = self.previous_token
            right = self.parse_factor()
            expr = Binary(expr, operator, right)

        return expr

    def parse_factor(self) -> Expression:
        expr = self.parse_unary()

        while self.match(TokenType.STAR, TokenType.SLASH):
            operator = self.previous_token
            right = self.parse_unary()
            expr = Binary(expr, operator, right)

        return expr

    def parse_unary(self) -> Expression:
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = self.previous_token
            right = self.parse_unary()
            return Unary(operator, right)

        return self.parse_primary()

    def parse_primary(self) -> Expression:
        if self.match(TokenType.TRUE):
            return Literal(True)
        if self.match(TokenType.FALSE):
            return Literal(False)
        if self.match(TokenType.NIL):
            return Literal(None)
        if self.match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self.previous_token.literal)
        if self.match(TokenType.LEFT_PAREN):
            expr = self.parse_expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)

        raise self.error(self.peek, "Expect expression.")
        
    def match(self, *types: TokenType) -> bool:
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False

    def consume(self, type: TokenType, error_message: str) -> Optional[Token]:
        if self.check(type):
            return self.advance()
        raise self.error(self.peek, error_message)

    def advance(self) -> Optional[Token]:
        if not self.is_at_end:
            self._current += 1
        return self.previous_token

    def check(self, type: TokenType) -> bool:
        if self.is_at_end:
            return False
        return self.peek.type == type

    def error(self, token: Token, message: str) -> ParseError: 
        from loxxx.lox import Lox
        
        Lox.error(token, message)
        return ParseError()

    @property
    def peek(self) -> Optional[Token]:
        return self._tokens[self._current]
    
    @property
    def previous_token(self) -> Optional[Token]:
        return self._tokens[self._current - 1] if self._current > 0 else None

    @property
    def is_at_end(self) -> bool:
        return self.peek.type == TokenType.EOF
