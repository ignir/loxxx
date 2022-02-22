import sys

from loxxx.lox import Lox


def main():
    args = sys.argv[1:]
    if len(args) > 1:
        print("Usage: loxxx [script]")
        exit(64)
    
    lox = Lox()
    if len(args) == 1:
        lox.run_file(args[0])
    else:
        lox.run_prompt()


if __name__ == "__main__":
    main()
