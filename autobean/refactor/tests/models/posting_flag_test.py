from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models


class TestPostingFlag:

    @pytest.mark.parametrize(
        'text', '*!&#?%PSTCURM',
    )
    def test_parse_success(self, text: str, parser: parser_lib.Parser) -> None:
        flag = parser.parse_token(text, raw_models.PostingFlag)
        assert flag.raw_text == text

    @pytest.mark.parametrize(
        'text', [
            'txn',
            '**',
            '!!',
            'A'
        ],
    )
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse_token(text, raw_models.PostingFlag)

    @pytest.mark.parametrize(
        'text,new_text', [
            ('*', '!'),
            ('!', '*'),
        ],
    )
    def test_set_raw_text(self, text: str, new_text: str, parser: parser_lib.Parser) -> None:
        flag = parser.parse_token(text, raw_models.PostingFlag)
        assert flag.raw_text == text
        flag.raw_text = new_text
        assert flag.raw_text == new_text

    @pytest.mark.parametrize(
        'text,new_value', [
            ('*', '!'),
            ('!', '*'),
        ],
    )
    def test_set_value(self, text: str, new_value: str, parser: parser_lib.Parser) -> None:
        flag = parser.parse_token(text, raw_models.PostingFlag)
        assert flag.value == text
        flag.value = new_value
        assert flag.value == new_value
        assert flag.raw_text == new_value
