from typing import Type, TypeVar
from .. import base

_TT = TypeVar('_TT', bound=Type[base.RawTokenModel])
_UT = TypeVar('_UT', bound=Type[base.RawTreeModel])


TOKEN_MODELS: dict[str, Type[base.RawTokenModel]] = {}
TREE_MODELS: dict[str, Type[base.RawTreeModel]] = {}


def token_model(cls: _TT) -> _TT:
    TOKEN_MODELS[cls.RULE] = cls
    return cls


def tree_model(cls: _UT) -> _UT:
    TREE_MODELS[cls.RULE] = cls
    return cls
