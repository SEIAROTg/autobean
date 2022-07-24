from lark import exceptions
import pytest
from autobean.refactor.models import raw_models
from . import base


class TestTransactionFlag(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text', '*!&#?%PSTCURM',
    )
    def test_parse_success(self, text: str) -> None:
        flag = self.raw_parser.parse_token(text, raw_models.TransactionFlag)
        assert flag.raw_text == text
        assert flag.value == text
        self.check_deepcopy_token(flag)

    def test_parse_success_txn(self) -> None:
        flag = self.raw_parser.parse_token('txn', raw_models.TransactionFlag)
        assert flag.raw_text == 'txn'
        assert flag.value == '*'

    @pytest.mark.parametrize(
        'text', [
            'TXN',
            '**',
            '!!',
            'A'
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.raw_parser.parse_token(text, raw_models.TransactionFlag)

    @pytest.mark.parametrize(
        'text,new_text', [
            ('*', '!'),
            ('!', '*'),
            ('*', 'txn'),
            ('!', 'txn'),
            ('txn', '!'),
            ('txn', '*'),
        ],
    )
    def test_set_raw_text(self, text: str, new_text: str) -> None:
        flag = self.raw_parser.parse_token(text, raw_models.TransactionFlag)
        assert flag.raw_text == text
        flag.raw_text = new_text
        assert flag.raw_text == new_text

    @pytest.mark.parametrize(
        'text,expected_value,new_value', [
            ('*', '*', '!'),
            ('!', '!', '*'),
            ('txn', '*', '!'),
            ('txn', '*', '*'),
        ],
    )
    def test_set_value(self, text: str, expected_value: str, new_value: str) -> None:
        flag = self.raw_parser.parse_token(text, raw_models.TransactionFlag)
        assert flag.value == expected_value
        flag.value = new_value
        assert flag.value == new_value
        assert flag.raw_text == new_value
