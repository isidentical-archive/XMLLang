import ast
import re
import operator

from typing import Union, NewType, Sequence, Tuple, List
from itertools import chain
from functools import partial
from distutils.util import strtobool
from xmllang.parser.semantic import *

c = re.compile

Patterns = (c(r"True|False|None"), c(r"^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)$"), r"\.\.\.")
Literals = (ast.NameConstant, ast.Num, ast.Ellipsis)
AstMap = tuple(zip(Patterns, Literals))

AnyAst = NewType("Any AST Object", ast.AST)
LiteralType = NewType("AST Literal", Union[Literals])
SequenceType = NewType("AST Sequence", Union[ast.List, ast.Tuple, ast.Set])
MappingType = NewType("AST Mapping", ast.Dict)


@SemanticRule.register
class ExprDecl:
    """Expression declaration, everything counts as an expression
    in XMLLang standards.
    """

    _type = SemanticType("Expression", SemanticMod.EXPR)

    def __init__(self, expr):
        self.expr = expr
        self.element = expr.expr

    def make(self) -> None:
        pass

    def pattern(self) -> None:
        pass


@SemanticRule.register
class ElementDecl(ExprDecl):
    """Element declaration, consists from values."""

    _type = SemanticType("Element", SemanticMod.TEXT_ATTR)

    def make(self) -> AnyAst:
        if len(self.element) != 0:
            if strtobool(self.element.attrib.get("f", "false")):
                return FStringDecl(self.expr)
                # raise NotImplementedError("FStrings are not implemented")
            elif len(self.expr.children) == 1:
                ex = self.expr.children[0]
                return get_decl(ex.expr.tag)(ex).make()
            else:
                raise SyntaxError("Unkown behaivor")

        casts = self.element.attrib.get("cast")
        value = self.element.text.strip()

        if casts:
            if casts == "bytes":
                value = bytes(value, self.element.attrib.get("encoding", "utf-8"))

            if hasattr(ast, casts.title()):
                return getattr(ast, casts.title())(value)
            else:
                raise SyntaxError(f"Couldn't cast to {casts}")

        for pattern, literal in AstMap:
            match = re.match(pattern, value)
            if match:
                val = self.typecast(match, literal)
                if val:
                    return literal(val)
                else:
                    return literal()
        else:
            return ast.Str(value)

    @staticmethod
    def typecast(match, literal):
        if literal is ast.NameConstant:
            m = match.group(0)
            if m in {"True", "False"}:
                return strtobool(m)
            else:
                return None
        elif literal is ast.Num:
            m = match.group(0)
            if "." in m:
                return float(m)
            else:
                return int(m)
        else:
            return None


class FStringDecl(ExprDecl):
    def make(self) -> ast.JoinedStr:
        text = self.element.text

        if isinstance(text, str):
            text = text.strip()

        base = [ast.Str(text)] if text else []
        children = map(
            partial(ast.FormattedValue, conversion=-1, format_spec=None),
            map(operator.attrgetter("value"), self.expr.children),
        )
        texts = map(
            ast.Str, map(str.strip, map(operator.attrgetter("tail"), self.element))
        )
        base.extend(chain.from_iterable(zip(children, texts)))

        return ast.JoinedStr(base)


class SequenceDecl(ExprDecl):

    _type = SemanticType("NaRT", SemanticMod.SUB_ELM_ATTR)  # Not a Real Type

    def make(self) -> SequenceType:
        pass

    def get_ctx(self) -> Union[ast.Load, ast.Store]:
        return getattr(
            ast,
            self.element.attrib.get("ctx", self.expr.meta.get("ctx", "load")).title(),
            ast.Load,
        )()

    def get_elts(self) -> Sequence[ast.AST]:
        return [e.value for e in self.expr.children if isinstance(e.value, ast.AST)]


@SemanticRule.register
class ListDecl(SequenceDecl, ExprDecl):
    """List declaration"""

    _type = SemanticType("List", SemanticMod.SUB_ELM_ATTR)

    def make(self) -> ast.List:
        return ast.List(self.get_elts(), self.get_ctx())


@SemanticRule.register
class TupleDecl(SequenceDecl, ExprDecl):
    """Tuple Declaration"""

    _type = SemanticType("Tuple", SemanticMod.SUB_ELM_ATTR)

    def make(self) -> ast.Tuple:
        return ast.Tuple(self.get_elts(), self.get_ctx())


@SemanticRule.register
class SetDecl(SequenceDecl, ExprDecl):
    """Set declaration"""

    _type = SemanticType("Set", SemanticMod.SUB_ELM_ATTR)

    def make(self) -> ast.Set:
        return ast.Set(self.get_elts())


class MappingDecl(ExprDecl):
    _type = SemanticType("NaRT", SemanticMod.SUB_ELM_ATTR)

    def __init__(self, expr):
        super().__init__(expr)

        pairs = self.get_pairs()
        self.keys = list(map(operator.itemgetter(0), pairs))
        self.values = list(map(operator.itemgetter(1), pairs))

    def make(self) -> MappingType:
        pass

    def get_pairs(self) -> List[Tuple[ast.Str, AnyAst]]:
        pairs = [
            e.value
            for e in self.expr.children
            if isinstance(e.value[0], ast.Str) and isinstance(e.value[1], ast.AST)
        ]
        return pairs


@SemanticRule.register
class DictDecl(MappingDecl, ExprDecl):
    """Dict declaration"""

    _type = SemanticType("Dict", SemanticMod.SUB_ELM_ATTR)

    def make(self) -> ast.Dict:
        return ast.Dict(self.keys, self.values)


@SemanticRule.register
class DictItemDecl(ElementDecl, ExprDecl):
    """Dict Item declaration"""

    _type = SemanticType("DictItem", SemanticMod.TEXT_ATTR)

    def make(self) -> Tuple[ast.Str, AnyAst]:
        key = ast.Str(self.element.attrib["name"])
        value = super().make()

        return key, value


@SemanticRule.register
class NameDecl(ElementDecl, ExprDecl):
    """Name declaration"""

    _type = SemanticType(
        "Name", SemanticModUnion[SemanticMod.TEXT_ATTR, SemanticMod.NO_TEXT_ATTR]
    )

    def make(self) -> ast.Name:
        text = self.element.text
        call = strtobool(self.element.attrib.get("call", "False"))
        
        if isinstance(text, str):
            text = text.strip()

        if not text:
            val = ast.Name(self.element.tag, ast.Load())
            spec = self.get_spec()
            if call:
                return ast.Call(val, *spec)
            else:
                return val
        else:
            return ast.Assign([ast.Name(self.element.tag, ast.Store())], super().make())

    def get_spec(self) -> Tuple:
        args = []
        kwargs = []

        for e in self.expr.children:
            v = e.value
            if e.expr.tag == 'attr':
                self.add_attr(e)
            else:
                if isinstance(v, tuple):
                    kwargs.append(ast.keyword(v[0].s, v[1]))
                else:
                    args.append(v)

        return args, kwargs
    
    def add_attr(self, attr) -> None:
        pass
        
SemanticMap = {
    "e": ElementDecl,
    "list": ListDecl,
    "tuple": TupleDecl,
    "set": SetDecl,
    "dict": DictDecl,
    "item": DictItemDecl,
    "fstring": FStringDecl,
}


def get_decl(tag):
    try:
        return SemanticMap[tag]
    except KeyError:
        return NameDecl
