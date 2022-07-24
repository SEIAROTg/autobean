from lark import exceptions
import pytest
from autobean.refactor.models import raw_models
from . import base


class TestAccount(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text', [
            'Assets:Foo',
            'Assets:Foo:Bar',
            'Assets:X',
            'Assets:X银行',
            # This is an invalid beancount account name but does pass beancount lexer.
            # The validation happens in the parser here: https://github.com/beancount/beancount/blob/89bf061b60777be3ae050c5c44fef67d93029130/beancount/parser/grammar.py#L243.
            'Assets:银行',
        ],
    )
    def test_parse_success(self, text: str) -> None:
        token = self.raw_parser.parse_token(text, raw_models.Account)
        assert token.raw_text == text
        assert token.value == text
        self.check_deepcopy_token(token)

    @pytest.mark.parametrize(
        'text', [
            'Assets',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.raw_parser.parse_token(text, raw_models.Account)

    def test_set_raw_text(self) -> None:
        token = self.raw_parser.parse_token('Assets:Foo', raw_models.Account)
        token.raw_text = 'Liabilities:Foo'
        assert token.raw_text == 'Liabilities:Foo'
        assert token.value == 'Liabilities:Foo'

    def test_set_value(self) -> None:
        token = self.raw_parser.parse_token('Assets:Foo', raw_models.Account)
        token.value = 'Liabilities:Foo'
        assert token.value == 'Liabilities:Foo'
        assert token.raw_text == 'Liabilities:Foo'
