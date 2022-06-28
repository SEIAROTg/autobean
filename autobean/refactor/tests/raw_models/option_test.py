from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models
from . import conftest


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

    def test_set_raw_key(self, parser: parser_lib.Parser, print_model: conftest.PrintModel) -> None:
        option = parser.parse('option  "key"    "value"', raw_models.Option)
        new_key = parser.parse_token('"new_key"', raw_models.EscapedString)
        option.raw_key = new_key
        assert option.raw_key is new_key
        assert print_model(option) == 'option  "new_key"    "value"'

    def test_set_raw_value(self, parser: parser_lib.Parser, print_model: conftest.PrintModel) -> None:
        option = parser.parse('option  "key"    "value"', raw_models.Option)
        new_value = parser.parse_token('"new_value"', raw_models.EscapedString)
        option.raw_value = new_value
        assert option.raw_value is new_value
        assert print_model(option) == 'option  "key"    "new_value"'

    def test_noop_set_raw_key(self, parser: parser_lib.Parser, print_model: conftest.PrintModel) -> None:
        option = parser.parse('option  "key"    "value"', raw_models.Option)
        initial_key = option.raw_key
        option.raw_key = option.raw_key
        assert option.raw_key is initial_key
        assert print_model(option) == 'option  "key"    "value"'

    def test_reuse_active_token(self, parser: parser_lib.Parser) -> None:
        option = parser.parse('option  "key" "value"', raw_models.Option)
        with pytest.raises(ValueError):
            option.raw_key = option.raw_value
    
    def test_reuse_inactive_token(self, parser: parser_lib.Parser, print_model: conftest.PrintModel) -> None:
        option = parser.parse('option  "key"    "value"', raw_models.Option)
        initial_key = option.raw_key
        option.raw_key = parser.parse_token('"new_key"', raw_models.EscapedString)
        option.raw_key = initial_key
        assert option.raw_key is initial_key
        assert print_model(option) == 'option  "key"    "value"'
    