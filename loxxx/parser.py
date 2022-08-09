from typing import List, Optional, cast

from loxxx.expressions import Assign, Binary, Expression, Grouping, Literal, Logical, Unary, Variable
from loxxx.scanner import Token, TokenType
from loxxx.statements import Block, ExpressionStatement, If, Statement, PrintStatement, VariableDeclaration, While


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._current = 0

    def parse(self) -> List[Statement | None]:
        statements = []
        while not self.is_at_end:
            statements.append(self.parse_declaration())
        return statements

    def parse_declaration(self) -> Optional[Statement]:
        try:
            if self.match(TokenType.VAR):
                return self.parse_var_declaration()
            return self.parse_statement()
        except ParseError:
            self._synchronize()
            return None

    def parse_var_declaration(self) -> VariableDeclaration:
        name = self.consume(TokenType.IDENTIFIER, "Expect a variable name.")
        initializer = None
        if self.match(TokenType.EQUAL):
            initializer = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after a variable declaration.")
        return VariableDeclaration(name, initializer)

    def parse_statement(self) -> Statement:
        if self.match(TokenType.FOR):
            return self.parse_for_statement()
        if self.match(TokenType.IF):
            return self.parse_if_statement()
        if self.match(TokenType.PRINT):
            return self.parse_print_statement()
        if self.match(TokenType.WHILE):
            return self.parse_while_statement()
        if self.match(TokenType.LEFT_BRACE):
            return Block(self.parse_block_statement())  # type: ignore[arg-type]
        return self.parse_expression_statement()

    def parse_for_statement(self) -> While:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'for'.")

        if self.match(TokenType.SEMICOLON):
            initializer = None
        elif self.match(TokenType.VAR):
            initializer = self.parse_var_declaration()
        else:
            initializer = self.parse_expression_statement()

        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after loop condition.")

        increment = None
        if not self.check(TokenType.RIGHT_PAREN):
            increment = self.parse_expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after for clauses.")

        body = self.parse_statement()
        if increment:
            body = Block([body, ExpressionStatement(increment)])

        if not condition:
            condition = Literal(True)
        body = While(condition, body)

        if initializer:
            body = Block([initializer, body])

        return body

    def parse_if_statement(self) -> If:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'if'.")
        condition = self.parse_expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after if condition.")

        then_branch = self.parse_statement()
        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.parse_statement()

        return If(condition, then_branch, else_branch)

    def parse_print_statement(self) -> PrintStatement:
        value = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after a value.")
        return PrintStatement(value)

    def parse_while_statement(self) -> While:
        self.consume(TokenType.LEFT_PAREN, "Expect '(' after 'while'.")
        condition = self.parse_expression()
        self.consume(TokenType.RIGHT_PAREN, "Expect ')' after while condition.")
        body = self.parse_statement()
        return While(condition, body)

    def parse_expression_statement(self) -> ExpressionStatement:
        expr = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expect ';' after an expression.")
        return ExpressionStatement(expr)

    def parse_block_statement(self) -> List[Statement | None]:
        statements = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end:
            statements.append(self.parse_declaration())
        self.consume(TokenType.RIGHT_BRACE, "Expect '}' after block.")
        return statements

    def parse_expression(self) -> Expression:
        return self.parse_assignment()

    def parse_assignment(self) -> Expression:
        expr = self.parse_or()

        if self.match(TokenType.EQUAL):
            equals = cast(Token, self.previous_token)
            value = self.parse_assignment()

            if isinstance(expr, Variable):
                return Assign(expr.name, value)
            self.error(equals, "Invalid assignment target.")

        return expr

    def parse_or(self) -> Expression:
        expr = self.parse_and()

        while self.match(TokenType.OR):
            operator = self.previous_token
            right = self.parse_and()
            expr = Logical(expr, operator, right)

        return expr

    def parse_and(self) -> Expression:
        expr = self.parse_equality()

        while self.match(TokenType.AND):
            operator = self.previous_token
            right = self.parse_equality()
            expr = Logical(expr, operator, right)

        return expr

    def parse_equality(self) -> Expression:
        expr = self.parse_comparison()

        while self.match(TokenType.BANG_EQUAL, TokenType.EQUAL_EQUAL):
            operator = cast(Token, self.previous_token)
            right = self.parse_comparison()
            expr = Binary(expr, operator, right)

        return expr

    def parse_comparison(self) -> Expression:
        expr = self.parse_term()

        while self.match(TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL):
            operator = cast(Token, self.previous_token)
            right = self.parse_term()
            expr = Binary(expr, operator, right)

        return expr

    def parse_term(self) -> Expression:
        expr = self.parse_factor()

        while self.match(TokenType.MINUS, TokenType.PLUS):
            operator = cast(Token, self.previous_token)
            right = self.parse_factor()
            expr = Binary(expr, operator, right)

        return expr

    def parse_factor(self) -> Expression:
        expr = self.parse_unary()

        while self.match(TokenType.STAR, TokenType.SLASH):
            operator = cast(Token, self.previous_token)
            right = self.parse_unary()
            expr = Binary(expr, operator, right)

        return expr

    def parse_unary(self) -> Expression:
        if self.match(TokenType.BANG, TokenType.MINUS):
            operator = cast(Token, self.previous_token)
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
            return Literal(cast(Token, self.previous_token).literal)
        if self.match(TokenType.IDENTIFIER):
            return Variable(cast(Token, self.previous_token))
        if self.match(TokenType.LEFT_PAREN):
            expr = self.parse_expression()
            self.consume(TokenType.RIGHT_PAREN, "Expect ')' after expression.")
            return Grouping(expr)

        raise self.error(self.peek, "Expect expression.")

    def match(self, *types: TokenType) -> bool:
        """If current token is of one of the specified types consume it and return True"""
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False

    def consume(self, type: TokenType, error_message: str) -> Token:
        if self.check(type):
            return cast(Token, self.advance())
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
        # TODO: Can this work without circular dependencies between classes?
        from loxxx.lox import Lox

        Lox.error(token, message)
        return ParseError()

    def _synchronize(self) -> None:
        self.advance()
        new_statement_tokens = {
            TokenType.CLASS,
            TokenType.FUN,
            TokenType.VAR,
            TokenType.FOR,
            TokenType.IF,
            TokenType.WHILE,
            TokenType.PRINT,
            TokenType.RETURN,
        }
        while not self.is_at_end:
            if cast(Token, self.previous_token).type == TokenType.SEMICOLON:
                return
            if self.peek.type in new_statement_tokens:
                return
            self.advance()

    @property
    def peek(self) -> Token:
        return self._tokens[self._current]

    @property
    def previous_token(self) -> Optional[Token]:
        return self._tokens[self._current - 1] if self._current > 0 else None

    @property
    def is_at_end(self) -> bool:
        return self.peek.type == TokenType.EOF
