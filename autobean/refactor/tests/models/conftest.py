import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models


@pytest.fixture(scope='package')
def raw_parser() -> parser_lib.Parser:
    return parser_lib.Parser(raw_models.TOKEN_MODELS, raw_models.TREE_MODELS)


@pytest.fixture(scope='package')
def easy_parser() -> parser_lib.Parser:
    return parser_lib.Parser(easy_models.TOKEN_MODELS, easy_models.TREE_MODELS)
