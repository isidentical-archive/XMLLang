from __future__ import annotations

import ast
import os
import xml.etree.ElementTree as ET

from collections import defaultdict, OrderedDict
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Optional
from pprint import pprint
from reprlib import recursive_repr

from xmllang.parser.semantics import SemanticMap


@dataclass(unsafe_hash=True)
class XMLExpr:
    expr: ET.Element
    value: Optional[ast.AST] = None
    
    parent: Optional[XMLExpr] = None
    children: Optional[Sequence[XMLExpr]] = field(default_factory=list, hash=False)
    
    meta: Optional[Dict] = field(default_factory=dict, hash=False)
    
    @recursive_repr()
    def __repr__(self):
        if self.parent:
            qualname = f"{self.parent!r}.{self.expr.tag}"
        else:
            qualname = self.expr.tag
        return qualname
    
    def __str__(self):
        return repr(self)
        
class Parser:
    """Parses XML files and converts them into Python AST 
    with XMLLang standards."""
    def __init__(self, xml: ET.ElementTree) -> None:
        self.xml = xml
        self.root = self.xml.getroot()
        self.tracer = 0
        
    @classmethod
    def fromfile(cls, file_name: os.PathLike) -> Parser:
        """Creates an :py:class:`Parser` instance from a file
        instead of an already existing XML object.
        """
        xml = ET.parse(os.fspath(file_name))
        return cls(xml)
        
    def parse(self, root: Optional[ET.Element] = None) -> ast.Module:
        """Runs through instance's root (xml's root) attribute.
        Tracks contexts and returns result of :py:func:`build_module`
        """        

        root = root or self.root
        points = self._parse(root, defaultdict(dict), 0)
        points = OrderedDict(reversed(list(points.items())))
        
        return self.build_module(points)
    
    def build_module(self, points: Dict[int, Sequence[XMLExpr]]) -> ast.Module:
        """Builds an ast.Module instance with given parse tree"""
        
        xmlast = deepcopy(points)
        
        for level, point in points.items():
            xmlast[level] = []
            
            for encap, exprs in point.items():
                
                for expr in exprs:
                    expr.value = self.xmleval(expr)
                
                encap.value = self.xmleval(encap)
                xmlast[level].append(encap)
            
        content = []
        for expr in xmlast[0]:
            content.append(ast.Expr(expr.value))
        
        module = ast.Module(content)
        ast.fix_missing_locations(module)

        return module
    
    def _parse(self, root: ET.Element, ctx: Dict, level: int = 0, bind_to: Optional[XMLExpr] = None) -> Dict:
        for node in root:
            expr = XMLExpr(node, bind_to)
            
            if bind_to is not None:
                bind_to.children.append(expr)

            if len(node) == 0:
                if bind_to:
                    ptr = ctx[level-1][bind_to]
                    
                    if not isinstance(ptr, list):
                        ptr = [ptr]
                    
                    ptr.append(expr)
                        
                else:
                    ctx[level][expr] = [expr]
            else:
                ctx[level][expr] = []
                ctx = self._parse(node, ctx, level + 1, expr)
        else:
            return ctx

    def xmleval(self, expr: XMLExpr) -> ast.AST:
        semantic = SemanticMap[expr.expr.tag](expr)
        ast = semantic.make()
        return ast
        
    def __str__(self):
        return f"{self.file_path} parser"

    def __repr__(self):
        return f"Parser({self.file_path})"
    
    __call__ = parse
    __getitem__ = lambda s, _ : s.root.__getitem__(_)
