from lark import exceptions
import pytest
from autobean.refactor.models import raw_models
from . import base


class TestTag(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,value', [
            ('#foo', 'foo'),
            ('#XX.YY', 'XX.YY'),
            ('#000', '000'),
        ],
    )
    def test_parse_success(self, text: str, value: str) -> None:
        token = self.raw_parser.parse_token(text, raw_models.Tag)
        assert token.raw_text == text
        assert token.value == value
        self.check_deepcopy_token(token)

    @pytest.mark.parametrize(
        'text', [
            'foo',
            '#标签',
            '#x!',
            '^foo',
            '##foo',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.raw_parser.parse_token(text, raw_models.Tag)

    def test_set_raw_text(self) -> None:
        token = self.raw_parser.parse_token('#foo', raw_models.Tag)
        token.raw_text = '#bar'
        assert token.raw_text == '#bar'
        assert token.value == 'bar'

    def test_set_value(self) -> None:
        token = self.raw_parser.parse_token('#foo', raw_models.Tag)
        token.value = 'bar'
        assert token.value == 'bar'
        assert token.raw_text == '#bar'
