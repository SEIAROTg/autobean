from lark import exceptions
import pytest
from autobean.refactor.models import raw_models
from . import base


class TestPostingFlag(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text', '*!&#?%PSTCURM',
    )
    def test_parse_success(self, text: str) -> None:
        flag = self.raw_parser.parse_token(text, raw_models.PostingFlag)
        assert flag.raw_text == text
        self.check_deepcopy_token(flag)

    @pytest.mark.parametrize(
        'text', [
            'txn',
            '**',
            '!!',
            'A'
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.raw_parser.parse_token(text, raw_models.PostingFlag)

    @pytest.mark.parametrize(
        'text,new_text', [
            ('*', '!'),
            ('!', '*'),
        ],
    )
    def test_set_raw_text(self, text: str, new_text: str) -> None:
        flag = self.raw_parser.parse_token(text, raw_models.PostingFlag)
        assert flag.raw_text == text
        flag.raw_text = new_text
        assert flag.raw_text == new_text

    @pytest.mark.parametrize(
        'text,new_value', [
            ('*', '!'),
            ('!', '*'),
        ],
    )
    def test_set_value(self, text: str, new_value: str) -> None:
        flag = self.raw_parser.parse_token(text, raw_models.PostingFlag)
        assert flag.value == text
        flag.value = new_value
        assert flag.value == new_value
        assert flag.raw_text == new_value
