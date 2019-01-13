from inspect import signature as sgn
from ast import AST
from abc import ABC, abstractmethod
from typing import Union, Tuple, Optional, Any, Pattern
from dataclasses import dataclass
from enum import Enum, auto

class SemanticMod(Enum):
    NO_TEXT = auto()
    NO_TEXT_ATTR = auto() # <coding style="utf8" /> 
    
    SUB_ELM = auto()
    SUB_ELM_ATTR = auto()
    
    TEXT = auto()
    TEXT_ATTR = auto() # <e>ABC</e>

    EXPR = auto() # Escape method like typing.Any
    
@dataclass
class SemanticType:
    name: str
    mod : Union[SemanticMod, Tuple[SemanticMod, ...]]
    meta: Optional[Any] = None

class SemanticRule(ABC):
    @abstractmethod
    def make(self) -> AST:
        """Transpiles XMLLang to python AST"""
        pass

def gendoc(klass):
    if hasattr(klass, 'make'):
        make = getattr(klass, 'make')
        signature = sgn(make)
        signature = signature.return_annotation
        make.__doc__ = f"Constructs {signature.__name__ if hasattr(signature, '__name__') else signature} from given XML Element."
    else:
        raise ValueError('Class doesn\'t have any make method')
