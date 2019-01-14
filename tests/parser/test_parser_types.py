import ast
import unittest
import xml.etree.ElementTree as ET

from pathlib import Path
from astor.code_gen import to_source
from astpretty import pprint
from xmllang.parser import Parser

PATH = Path(__file__).parent / "demo"


class TestParserTypes(unittest.TestCase):
    def get_xml(self, name):
        return ET.parse(PATH / "test_parser_types" / name)

    def test_simple_types(self):
        # string, integer, float, force casting
        xml = Parser(self.get_xml("basic_types.xml"))
        module = xml.parse()
        code = compile(module, "<ast>", "exec")

        mymodule = ast.Module(
            [
                ast.Expr(ast.Str("batuhan")),
                ast.Expr(ast.Num(15)),
                ast.Expr(ast.Num(15.5)),
                ast.Expr(ast.Str("13")),
                ast.Expr(ast.Ellipsis()),
                ast.Expr(ast.Bytes(bytes("a", "ASCII"))),
                ast.Expr(ast.Bytes(bytes("ş", "utf-8"))),
            ]
        )
        ast.fix_missing_locations(mymodule)
        mycode = compile(mymodule, "<ast>", "exec")
        pprint(mymodule)

        self.assertEqual(code, mycode)

    def test_sequence_types(self):
        # list, tuple, set, frozenset
        xml = Parser(self.get_xml("seq.xml"))
        module = xml.parse()
        code = compile(module, "<ast>", "exec")

        mymodule = ast.Module(
            [
                ast.Expr(
                    ast.List(
                        [
                            ast.Str("Batuhan"),
                            ast.Num(123),
                            ast.Num(323.23),
                            ast.List(
                                [
                                    ast.Num(235),
                                    ast.Tuple(
                                        [
                                            ast.Str("15"),
                                            ast.Set(
                                                [ast.Num(1), ast.Num(2), ast.Num(3)]
                                            ),
                                        ],
                                        ast.Load(),
                                    ),
                                ],
                                ast.Load(),
                            ),
                        ],
                        ast.Load(),
                    )
                ),
                ast.Expr(
                    ast.List(
                        [
                            ast.Str("Osman"),
                            ast.Num(321),
                            ast.Num(3333.333),
                            ast.List(
                                [
                                    ast.Num(532),
                                    ast.Tuple(
                                        [
                                            ast.Str("51"),
                                            ast.Set(
                                                [ast.Num(3), ast.Num(2), ast.Num(1)]
                                            ),
                                        ],
                                        ast.Load(),
                                    ),
                                ],
                                ast.Load(),
                            ),
                        ],
                        ast.Load(),
                    )
                ),
            ]
        )
        ast.fix_missing_locations(mymodule)
        mycode = compile(mymodule, "<ast>", "exec")

        self.assertEqual(code, mycode)

    def test_mapping_types(self):
        # dict
        xml = Parser(self.get_xml("dict.xml"))
        module = xml.parse()
        code = compile(module, "<ast>", "exec")

        mymodule = ast.Module(
            [
                ast.Expr(
                    ast.Dict(
                        [ast.Str("name"), ast.Str("age"), ast.Str("address")],
                        [
                            ast.Str("Batuhan"),
                            ast.Num(15),
                            ast.Dict(
                                [
                                    ast.Str("country"),
                                    ast.Str("city"),
                                    ast.Str("postalcode"),
                                ],
                                [
                                    ast.Str("Turkey"),
                                    ast.Dict(
                                        [ast.Str("primary"), ast.Str("secondary")],
                                        [ast.Str("Mersin"), ast.Str("Konya")],
                                    ),
                                    ast.Num(3333),
                                ],
                            ),
                        ],
                    )
                )
            ]
        )
        ast.fix_missing_locations(mymodule)
        mycode = compile(mymodule, "<ast>", "exec")

        self.assertEqual(code, mycode)


if __name__ == "__main__":
    unittest.main()
