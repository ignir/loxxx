from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loxxx.scanner import Token


def error(line: int, message: str):
    report(line, "", message)

def report(line: int, where: str, message: str):
    print(f"[line {line}] Error {where}: {message}")

class LoxRuntimeError(Exception):
    def __init__(self, token: 'Token', message: str):
        self.token = token
        self.message = message

    def __str__(self):
        return f"{self.token.lexeme}: {self.message}"
