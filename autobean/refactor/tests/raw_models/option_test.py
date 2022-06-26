from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models


class TestOption:

    @pytest.mark.parametrize(
        'text,key,value', [
            ('option "foo" "bar"', 'foo', 'bar'),
            ('option    "foo"    "multiple\nlines"', 'foo', 'multiple\nlines'),
        ],
    )
    def test_parse_success(self, text: str, key: str, value: str, parser: parser_lib.Parser) -> None:
        option = parser.parse(text, raw_models.Option)
        assert option.first_token.raw_text == 'option'
        assert option.raw_key.value == key
        assert option.raw_value.value == value
        assert option.last_token is option.raw_value

    @pytest.mark.parametrize(
        'text', [
            '    option "foo" "bar"',
            'option "foo"\n"bar"',
            'option "foo" "bar" "baz"',
            'option "foo"',
            'option ',
        ],
    )
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse(text, raw_models.Option)
