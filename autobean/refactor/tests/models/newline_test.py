from lark import exceptions
import pytest
from autobean.refactor.models import raw_models
from . import base


class TestNewline(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text', [
            '\n',
            '\r\n',
            '\r\r\n',
        ],
    )
    def test_parse_success(self, text: str) -> None:
        token = self._parser.parse_token(text, raw_models.Newline)
        assert token.raw_text == text

    @pytest.mark.parametrize(
        'text', [
            '\r',
            '\n ',
            '\n\r',
            '',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self._parser.parse_token(text, raw_models.Newline)
