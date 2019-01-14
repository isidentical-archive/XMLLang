import ast
import unittest
import xml.etree.ElementTree as ET

from pathlib import Path
from astor.code_gen import to_source
from astpretty import pprint
from xmllang.parser import Parser

PATH = Path(__file__).parent / "demo"


class TestParserNames(unittest.TestCase):
    def get_xml(self, name):
        return ET.parse(PATH / "test_parser_names" / name)

    def test_basic(self):
        xml = Parser(self.get_xml("basic.xml"))
        module = xml.parse()
        code = compile(module, "<ast>", "exec")

        mymodule = ast.Module(
            [
                ast.Assign([ast.Name("age", ast.Store())], ast.Num(15)),
                ast.Expr(ast.Name("age", ast.Load())),
                ast.Assign([ast.Name("name", ast.Store())], ast.Str("Batuhan")),
                ast.Expr(ast.Name("name", ast.Load())),
            ]
        )
        ast.fix_missing_locations(mymodule)
        mycode = compile(mymodule, "<ast>", "exec")

        self.assertEqual(code, mycode)


if __name__ == "__main__":
    unittest.main()
