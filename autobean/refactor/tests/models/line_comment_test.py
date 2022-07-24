from lark import exceptions
import pytest
from autobean.refactor.models import raw_models
from . import base


class TestComment(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text', [
            ';foo',
            '; foo',
            '; 你好!',
            ';',
            ';"',
            ';""',
            ' ;foo',
            ';foo\n',
            ' ;foo\n',
        ],
    )
    def test_parse_success(self, text: str) -> None:
        token = self.raw_parser.parse_token(text, raw_models.LineComment)
        assert token.raw_text == text
        self.check_deepcopy_token(token)

    @pytest.mark.parametrize(
        'text', [
            '\n;foo',
            '',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.raw_parser.parse_token(text, raw_models.LineComment)
