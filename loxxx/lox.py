from loxxx.scanner import Scanner


class Lox:
    def __init__(self):
        self._had_error = False

    def run_file(self, path):
        with open(path) as source_file:
            self.run(source_file.read())
        if self._had_error:
            exit(65)

    def run_prompt(self):
        while True:
            line = input("> ")
            if not line:
                break
            self.run(line)
            self._had_error = False

    def run(self, source):
        scanner = Scanner(source)
        tokens = scanner.scan()

        for token in tokens:
            print(token)
