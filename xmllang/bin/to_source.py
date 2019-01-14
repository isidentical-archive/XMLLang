from astor.code_gen import to_source
from xmllang.parser import Parser


def main(fname):
    p = Parser.fromfile(fname)
    m = p.parse()
    print(to_source(m))


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
