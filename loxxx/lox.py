import sys

from loxxx.errors import report
from loxxx.interpreter import Interpreter, LoxRuntimeError
from loxxx.parser import ParseError, Parser
from loxxx.scanner import Scanner, Token, TokenType


class Lox:
    _had_error = False
    _had_runtime_error = False

    _interpreter = Interpreter()

    def run_file(self, path):
        with open(path) as source_file:
            self.run(source_file.read())
        if Lox._had_error:
            exit(65)
        if Lox._had_runtime_error:
            exit(70)

    def run_prompt(self):
        while True:
            line = input("> ")
            if not line:
                break
            self.run(line, repl_mode=True)
            Lox._had_error = False

    def run(self, source, *, repl_mode=False):
        tokens = Scanner(source).scan()
        try:
            statements = Parser(tokens).parse()
        except ParseError as e:
            pass

        if Lox._had_error:
            return

        if repl_mode:
            self._interpreter.interpret_repl(statements)
        else:
            self._interpreter.interpret(statements)

    @staticmethod
    def error(token: Token, message: str) -> None:
        if token.type == TokenType.EOF:
            report(token.line_num, "at the end", message)
        else:
            report(token.line_num, f"at '{token.lexeme}'", message)
        Lox._had_error = True

    @staticmethod
    def runtime_error(error: LoxRuntimeError) -> None:
        print(f"{error} \n[line {error.token.line_num}]", file=sys.stderr)
        Lox._had_runtime_error = True
