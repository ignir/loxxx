from loxxx.ast_printer import ASTPrinter
from loxxx.errors import report
from loxxx.parser import Parser
from loxxx.scanner import Scanner, Token, TokenType


class Lox:
    _had_error = False
    
    def run_file(self, path):
        with open(path) as source_file:
            self.run(source_file.read())
        if Lox._had_error:
            exit(65)

    def run_prompt(self):
        while True:
            line = input("> ")
            if not line:
                break
            self.run(line)
            Lox._had_error = False

    def run(self, source):
        tokens = Scanner(source).scan()
        expression = Parser(tokens).parse()

        if Lox._had_error:
            return

        # TODO: Proper handling of parsing errors
        if not expression:
            return

        print(ASTPrinter().to_str(expression))

    @staticmethod
    def error(token: Token, message: str):
        if token.type == TokenType.EOF:
            report(token.line_num, " at end", message)
        else:
            report(token.line_num, f"at '{token.lexeme}'", message)
        Lox._had_error = True
