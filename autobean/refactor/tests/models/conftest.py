import io
from typing import Callable
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor import printer
from autobean.refactor.models import raw_models

PrintModel = Callable[[raw_models.RawModel], str]


@pytest.fixture(scope='package')
def parser() -> parser_lib.Parser:
    return parser_lib.Parser(raw_models.TOKEN_MODELS, raw_models.TREE_MODELS)


@pytest.fixture(scope='package')
def print_model() -> PrintModel:
    return lambda model: printer.print_model(model, io.StringIO()).getvalue()
