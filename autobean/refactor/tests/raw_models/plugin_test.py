from typing import Optional
from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models


class TestPlugin:

    @pytest.mark.parametrize(
        'text,name,config', [
            ('plugin "foo"', 'foo', None),
            ('plugin "foo" "bar"', 'foo', 'bar'),
            ('plugin    "foo"', 'foo', None),
            ('plugin    "foo"    "multiple\nlines"', 'foo', 'multiple\nlines'),
        ],
    )
    def test_parse_success(self, text: str, name: str, config: Optional[str], parser: parser_lib.Parser) -> None:
        plugin = parser.parse(text, raw_models.Plugin)
        assert plugin.first_token.raw_text == 'plugin'
        assert plugin.raw_name.value == name
        if config is None:
            assert plugin.raw_config is None
            assert plugin.last_token is plugin.raw_name
        else:
            assert plugin.raw_config
            assert plugin.raw_config.value == config
            assert plugin.last_token is plugin.raw_config

    @pytest.mark.parametrize(
        'text', [
            'plugin "foo" "bar" "baz"',
            'plugin ',
            '    plugin "foo"',
            'plugin\n"foo"',
        ],
    )
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse(text, raw_models.Plugin)
