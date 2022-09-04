import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor import models


@pytest.fixture(scope='package')
def parser() -> parser_lib.Parser:
    return parser_lib.Parser()
