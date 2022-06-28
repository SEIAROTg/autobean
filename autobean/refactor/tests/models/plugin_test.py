from typing import Optional
from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models
from . import conftest


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

    def test_set_raw_name(self, parser: parser_lib.Parser, print_model: conftest.PrintModel) -> None:
        plugin = parser.parse('plugin  "name"    "config"', raw_models.Plugin)
        new_name = parser.parse_token('"new_name"', raw_models.EscapedString)
        plugin.raw_name = new_name
        assert plugin.raw_name is new_name
        assert print_model(plugin) == 'plugin  "new_name"    "config"'

    def test_set_raw_config(self, parser: parser_lib.Parser, print_model: conftest.PrintModel) -> None:
        plugin = parser.parse('plugin  "name"    "config"', raw_models.Plugin)
        new_config = parser.parse_token('"new_config"', raw_models.EscapedString)
        plugin.raw_config = new_config
        assert plugin.raw_config is new_config
        assert print_model(plugin) == 'plugin  "name"    "new_config"'

    def test_remove_raw_config(self, parser: parser_lib.Parser, print_model: conftest.PrintModel) -> None:
        plugin = parser.parse('plugin  "name"    "config"', raw_models.Plugin)
        plugin.raw_config = None
        assert plugin.raw_config is None
        assert print_model(plugin) == 'plugin  "name"'

    def test_noop_remove_raw_config(self, parser: parser_lib.Parser, print_model: conftest.PrintModel) -> None:
        plugin = parser.parse('plugin  "name"', raw_models.Plugin)
        plugin.raw_config = None
        assert plugin.raw_config is None
        assert print_model(plugin) == 'plugin  "name"'

    def test_create_raw_config(self, parser: parser_lib.Parser, print_model: conftest.PrintModel) -> None:
        plugin = parser.parse('plugin  "name"', raw_models.Plugin)
        new_config = parser.parse_token('"new_config"', raw_models.EscapedString)
        plugin.raw_config = new_config
        assert plugin.raw_config is new_config
        assert print_model(plugin) == 'plugin  "name" "new_config"'
