from inspect import signature as sgn
from ast import AST
from abc import ABC, abstractmethod
from typing import Union, Tuple, Optional, Any, Pattern
from dataclasses import dataclass
from enum import Enum, auto


class SemanticMod(Enum):
    """Type of semantic declaration.
    
    - If semantic has no inside text it uses :py:class:`SemanticMod`.NO_TEXT* family
    - If semantic has no inside text but it has child elements it uses :py:class:`SemanticMod`.SUB_ELM* family
    - If semantic has text it uses :py:class:`SemanticMod`.TEXT* family
    
    And none of this is suitable for that semantic it uses an escape type, :py:class:`SemanticMod`.EXPR
    """

    NO_TEXT = auto()
    NO_TEXT_ATTR = auto()  # <coding style="utf8" />

    SUB_ELM = auto()
    SUB_ELM_ATTR = auto()

    TEXT = auto()
    TEXT_ATTR = auto()  # <e>ABC</e>

    EXPR = auto()  # Escape method like typing.Any


class ModUnion:
    def __getitem__(self, *args):
        pass


SemanticModUnion = ModUnion()


@dataclass
class SemanticType:
    name: str
    mod: Union[SemanticMod, Tuple[SemanticMod, ...]]
    meta: Optional[Any] = None


class SemanticRule(ABC):
    @abstractmethod
    def make(self) -> AST:
        """Transpiles XMLLang to python AST"""
        pass


def gendoc(klass):
    if hasattr(klass, "make"):
        make = getattr(klass, "make")
        signature = sgn(make)
        signature = signature.return_annotation
        make.__doc__ = f"Constructs {signature.__name__ if hasattr(signature, '__name__') else signature} from given XML Element."
    else:
        raise ValueError("Class doesn't have any make method")
