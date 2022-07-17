import io
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor import printer
from autobean.refactor.models import raw_models


class BaseTestModel:
    @pytest.fixture(autouse=True)
    def _setup_parser(self, parser: parser_lib.Parser) -> None:
        self._parser = parser

    def print_model(self, model: raw_models.RawModel) -> str:
        return printer.print_model(model, io.StringIO()).getvalue()
