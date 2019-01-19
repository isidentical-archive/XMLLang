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
class Expr:
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
class Element(Expr):
    """Element declaration, consists from values."""

    _type = SemanticType("Element", SemanticMod.TEXT_ATTR)

    def make(self) -> AnyAst:
        if len(self.element) != 0:
            if strtobool(self.element.attrib.get("f", "false")):
                return FString(self.expr)
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


class FString(Expr):
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


class Sequence(Expr):

    _type = SemanticType("NaRT", SemanticMod.SUB_ELM_ATTR)  # Not a Real Type

    def make(self) -> SequenceType:
        pass

    def get_declctx(self) -> Union[ast.Load, ast.Store]:
        return getattr(
            ast,
            self.element.attrib.get("ctx", self.expr.meta.get("ctx", "load")).title(),
            ast.Load,
        )()

    def get_declelts(self) -> Sequence[ast.AST]:
        return [e.value for e in self.expr.children if isinstance(e.value, ast.AST)]


@SemanticRule.register
class List(Sequence, Expr):
    """List declaration"""

    _type = SemanticType("List", SemanticMod.SUB_ELM_ATTR)

    def make(self) -> ast.List:
        return ast.List(self.get_declelts(), self.get_declctx())


@SemanticRule.register
class Tuple(Sequence, Expr):
    """Tuple declaration"""

    _type = SemanticType("Tuple", SemanticMod.SUB_ELM_ATTR)

    def make(self) -> ast.Tuple:
        return ast.Tuple(self.get_declelts(), self.get_declctx())


@SemanticRule.register
class Set(Sequence, Expr):
    """Set declaration"""

    _type = SemanticType("Set", SemanticMod.SUB_ELM_ATTR)

    def make(self) -> ast.Set:
        return ast.Set(self.get_declelts())


class Mapping(Expr):
    _type = SemanticType("NaRT", SemanticMod.SUB_ELM_ATTR)

    def __init__(self, expr):
        super().__init__(expr)

        pairs = self.get_declpairs()
        self.keys = list(map(operator.itemgetter(0), pairs))
        self.values = list(map(operator.itemgetter(1), pairs))

    def make(self) -> MappingType:
        pass

    def get_declpairs(self) -> List:
        pairs = [
            e.value
            for e in self.expr.children
            if isinstance(e.value[0], ast.Str) and isinstance(e.value[1], ast.AST)
        ]
        return pairs


@SemanticRule.register
class Dict(Mapping, Expr):
    """Dict declaration"""

    _type = SemanticType("Dict", SemanticMod.SUB_ELM_ATTR)

    def make(self) -> ast.Dict:
        return ast.Dict(self.keys, self.values)


@SemanticRule.register
class DictItem(Element, Expr):
    """Dict Item declaration"""

    _type = SemanticType("DictItem", SemanticMod.TEXT_ATTR)

    def make(self) -> Tuple:
        key = ast.Str(self.element.attrib["name"])
        value = super().make()

        return key, value


@SemanticRule.register
class Name(Element, Expr):
    """Name declaration"""

    _type = SemanticType(
        "Name", SemanticModUnion[SemanticMod.TEXT_ATTR, SemanticMod.NO_TEXT_ATTR]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attribs = []

    def make(self) -> ast.Name:
        text = self.element.text
        call = strtobool(self.element.attrib.get("call", "False"))

        if isinstance(text, str):
            text = text.strip()

        if not text:
            val = ast.Name(self.element.tag, ast.Load())
            spec = self.get_declspec(self.expr, self.add_attr)
            c = 0

            if call:
                val = ast.Call(val, *spec)
                c = 1

            if self.attribs:
                for attr in self.attribs:
                    t = attr[1].text.strip() if isinstance(attr[1].text, str) else None
                    if t:
                        val = ast.Assign(
                            [ast.Attribute(val, attr[2], ast.Store())],
                            Element(attr[0]).make(),
                        )
                    else:
                        val = ast.Attribute(val, attr[2], ast.Load())

                    if len(attr) == 4:
                        val = ast.Call(val, *attr[3])
                c = 1

            if not c:
                if len(self.element) == 1:
                    return ast.Assign(
                        [ast.Name(self.element.tag, ast.Store())],
                        Name(self.expr.children[0]).make(),
                    )

            return val

        else:
            target = ast.Name(self.element.tag, ast.Store())
            return ast.Assign([target], super().make())

    @staticmethod
    def get_declspec(expr, notifier) -> Tuple:
        args = []
        kwargs = []

        for e in expr.children:
            v = e.value
            if e.expr.tag == "attr":
                notifier(e)
            else:
                if isinstance(v, tuple):
                    kwargs.append(ast.keyword(v[0].s, v[1]))
                else:
                    args.append(v)

        return args, kwargs

    def add_attr(self, attr) -> None:
        val = attr.value
        self.attribs.append(val)


@SemanticRule.register
class Attribute(Element, Expr):
    _type = SemanticType("Attibute", SemanticMod.SUB_ELM_ATTR)

    def make(self) -> Tuple:
        """FYI it doesnt return a real ast.AST, it returns a tuple of python objects
        that we are going to use in Name.add_attr"""

        name = self.element.attrib["name"]
        call = strtobool(self.element.attrib.get("call", "False"))

        if call:
            spec = Name.get_declspec(self.expr, lambda e: None)
            return self.expr, self.element, name, spec
        else:
            return self.expr, self.element, name


SemanticMap = {
    "e": Element,
    "list": List,
    "tuple": Tuple,
    "set": Set,
    "dict": Dict,
    "item": DictItem,
    "fstring": FString,
    "attr": Attribute,
}


def get_decl(tag):
    try:
        return SemanticMap[tag]
    except KeyError:
        return Name
