import marshal
import os
import importlib.util
from pathlib import Path
from typing import Optional
from xmllang.parser import Parser

MAGIC_NUMBER = importlib.util.MAGIC_NUMBER


class Compiler:
    def compile(self, f: os.PathLike, to: Optional[os.PathLike] = None) -> int:
        """Takes filename and bytecode file destination and returns
        a status code"""

        f = Path(os.fspath(f))
        to = Path(os.fspath(to)) or f.with_suffix(".xmlc")

        parser = Parser.fromfile(f.resolve())
        module = parser.parse()

        code = compile(module, "<ast>", "exec")
        pyc = self._get_pyc(code)

        with open(to, "wb") as dest:
            dest.write(pyc)

        return 0

    def execute(self, f: os.PathLike):
        parser = Parser.fromfile(f)
        module = parser.parse()

        code = compile(module, "<ast>", "exec")
        exec(code)

    def _get_pyc(self, code, time=0, sourcesize=0):
        pyc = bytearray(MAGIC_NUMBER)
        pyc.extend(self._w_long(time))
        pyc.extend(self._w_long(sourcesize))
        pyc.extend(marshal.dumps(code))
        return pyc

    @staticmethod
    def _w_long(x):
        return (int(x) & 0xFFFFFFFF).to_bytes(4, "little")
