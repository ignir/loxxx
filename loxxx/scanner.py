import string
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

from loxxx.errors import error


class TokenType(Enum):
    # Single-character tokens.
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    DOT = auto()
    MINUS = auto()
    PLUS = auto()
    SEMICOLON = auto()
    SLASH = auto()
    STAR = auto()
    
    # One or two character tokens.
    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    
    # Literals.
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    
    # Keywords.
    AND = auto()
    CLASS = auto()
    ELSE = auto()
    FALSE = auto()
    FUN = auto()
    FOR = auto()
    IF = auto()
    NIL = auto()
    OR = auto()
    PRINT = auto()
    RETURN = auto()
    SUPER = auto()
    THIS = auto()
    TRUE = auto()
    VAR = auto()
    WHILE = auto()
    
    EOF = auto()


KEYWORD_TOKEN_TYPES = {
    "and": TokenType.AND,
    "class": TokenType.CLASS,
    "else": TokenType.ELSE,
    "false": TokenType.FALSE,
    "fun": TokenType.FUN,
    "for": TokenType.FOR,
    "if": TokenType.IF,
    "nil": TokenType.NIL,
    "or": TokenType.OR,
    "print": TokenType.PRINT,
    "return": TokenType.RETURN,
    "super": TokenType.SUPER,
    "this": TokenType.THIS,
    "true": TokenType.TRUE,
    "var": TokenType.VAR,
    "while": TokenType.WHILE,    
}


@dataclass
class Token:
    type: TokenType
    lexeme: str
    literal: Any
    line_num: int


class Scanner:
    def __init__(self, source):
        self._source = source
        self._tokens = []

        self._start = self._current = 0
        self._line_num = 1

    def scan(self):
        while not self._is_at_end():
            self._start = self._current
            self._scan_token()
        return self._tokens

    def _is_at_end(self):
        return self._current >= len(self._source)

    def _scan_token(self):
        match c := self._advance():
            case "(":
                self._add_token(TokenType.LEFT_PAREN)
            case ")":
                self._add_token(TokenType.RIGHT_PAREN)
            case "{":
                self._add_token(TokenType.LEFT_BRACE)
            case "}":
                self._add_token(TokenType.RIGHT_BRACE)
            case ",":
                self._add_token(TokenType.COMMA)
            case ".":
                self._add_token(TokenType.DOT)
            case "-":
                self._add_token(TokenType.MINUS)
            case "+":
                self._add_token(TokenType.PLUS)
            case ";":
                self._add_token(TokenType.SEMICOLON)
            case "*":
                self._add_token(TokenType.STAR)
            case "!":
                if self._match("="):
                    self._add_token(TokenType.BANG_EQUAL)
                else:
                    self._add_token(TokenType.BANG)
            case "=":
                if self._match("="):
                    self._add_token(TokenType.EQUAL_EQUAL)
                else:
                    self._add_token(TokenType.EQUAL)
            case "<":
                if self._match("="):
                    self._add_token(TokenType.LESS_EQUAL)
                else:
                    self._add_token(TokenType.LESS)
            case ">":
                if self._match("="):
                    self._add_token(TokenType.GREATER_EQUAL)
                else:
                    self._add_token(TokenType.GREATER)
            case "/":
                if self._match("/"):
                    # Consume comment line
                    while self._peek() not in ("\n", None):
                        self._advance()
                else:
                    self._add_token(TokenType.SLASH)
            case " " | "\r" | "\t":
                pass
            case "\n":
                self._line_num += 1
            case '"':
                self._scan_string()

            case _:
                if is_digit(c):
                    self._scan_number()
                elif is_alpha(c):
                    self._scan_identifier()
                else:
                    error(self._line_num, f"Unexpected character {c}.")

    def _advance(self) -> str:
        char = self._source[self._current]
        self._current += 1
        return char

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self._source[self._current] != expected:
            return False
        self._current += 1
        return True

    def _peek(self) -> Optional[str]:
        return None if self._is_at_end() else self._source[self._current]

    def _peek_next(self) -> Optional[str]:
        if self._current + 1 >= len(self._source):
            return None
        return self._source[self._current + 1]

    def _scan_string(self) -> None:
        while (next_char := self._peek()) != '"' and not self._is_at_end():
            if next_char == "\n":
                self._line_num += 1
            self._advance()
        
        if self._is_at_end():
            error(self._line_num, "Unterminated string")
            return

        # Consume closing "
        self._advance()

        # Trim the " surrounding the string
        self._add_token(TokenType.STRING, self._source[self._start + 1:self._current - 1])

    def _scan_number(self) -> None:
        while is_digit(self._peek()):
            self._advance()

        # Look for a fractional part.
        if self._peek() == "." and is_digit(self._peek_next()):
            # Consume the ".".
            self._advance()
            while is_digit(self._peek()):
                self._advance()

        self._add_token(TokenType.NUMBER, float(self._source[self._start:self._current]))

    def _scan_identifier(self) -> None:
        while is_alphanumeric(self._peek()):
            self._advance()

        text = self._source[self._start:self._current]
        token_type = KEYWORD_TOKEN_TYPES.get(text, TokenType.IDENTIFIER)
        self._add_token(token_type)
    
    def _add_token(self, token_type, literal=None) -> None:
        self._tokens.append(
            Token(
                type=token_type,
                lexeme=self._source[self._start:self._current],
                literal=literal,
                line_num=self._line_num,
            ),
        )


def is_digit(char: Optional[str]) -> bool:
    return char is not None and char in string.digits

def is_alpha(char: Optional[str]) -> bool:
    return char is not None and ('a' <= char <= 'z' or 'A' <= char <= 'Z' or char == "_")

def is_alphanumeric(char: Optional[str]) -> bool:
    return is_alpha(char) or is_digit(char)