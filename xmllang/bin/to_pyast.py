from astpretty import pprint
from xmllang.parser import Parser


def main(fname):
    p = Parser.fromfile(fname)
    m = p.parse()
    pprint(m)


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
