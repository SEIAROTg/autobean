from lark import exceptions
import pytest
from autobean.refactor import models
from . import base


class TestCurrency(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text', [
            'USD',
            'AAPL',
            'NT.TO',
            'TLT_040921C144',
            '/6J',
            '/NQH21',
            '/NQH21_QNEG21C13100',
            'C345',
            # These are technically invalid currencies but it's difficult to reject them under contextual lexer.
            'TRUE',
            'FALSE',
            'NULL',
        ],
    )
    def test_parse_success(self, text: str) -> None:
        token = self.parser.parse_token(text, models.Currency)
        assert token.raw_text == text
        assert token.value == text
        self.check_deepcopy_token(token)

    @pytest.mark.parametrize(
        'text', [
            '/6.3',
            '/CAC_',
            'C_',
            'V',  # it is valid in v3 syntax
            'Asset',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse_token(text, models.Currency)

    def test_set_raw_text(self) -> None:
        token = self.parser.parse_token('USD', models.Currency)
        token.raw_text = 'AAPL'
        assert token.raw_text == 'AAPL'
        assert token.value == 'AAPL'

    def test_set_value(self) -> None:
        token = self.parser.parse_token('USD', models.Currency)
        token.value = 'AAPL'
        assert token.value == 'AAPL'
        assert token.raw_text == 'AAPL'
