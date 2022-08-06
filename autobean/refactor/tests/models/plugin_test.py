from typing import Optional
from lark import exceptions
import pytest
from autobean.refactor import models
from . import base


class TestPlugin(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,name,config', [
            ('plugin "foo"', 'foo', None),
            ('plugin "foo" "bar"', 'foo', 'bar'),
            ('plugin    "foo"', 'foo', None),
            ('plugin    "foo"    "multiple\nlines"', 'foo', 'multiple\nlines'),
        ],
    )
    def test_parse_success(self, text: str, name: str, config: Optional[str]) -> None:
        plugin = self.parser.parse(text, models.Plugin)
        assert plugin.raw_name.value == name
        if config is None:
            assert plugin.raw_config is None
        else:
            assert plugin.raw_config
            assert plugin.raw_config.value == config
        assert self.print_model(plugin) == text
        self.check_deepcopy_tree(plugin)
        self.check_reattach_tree(plugin)

    @pytest.mark.parametrize(
        'text', [
            'plugIn "foo" "bar"',
            'plugin "foo" "bar" "baz"',
            'plugin ',
            '    plugin "foo"',
            'plugin\n"foo"',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Plugin)

    def test_set_raw_name(self) -> None:
        plugin = self.parser.parse('plugin  "name"    "config"', models.Plugin)
        new_name = models.EscapedString.from_value('new_name')
        plugin.raw_name = new_name
        assert plugin.raw_name is new_name
        assert self.print_model(plugin) == 'plugin  "new_name"    "config"'

    def test_set_name(self) -> None:
        plugin = self.parser.parse('plugin  "name"    "config"', models.Plugin)
        assert plugin.name == 'name'
        plugin.name = 'new_name'
        assert plugin.name == 'new_name'
        assert self.print_model(plugin) == 'plugin  "new_name"    "config"'

    def test_set_raw_config(self) -> None:
        plugin = self.parser.parse('plugin  "name"    "config"', models.Plugin)
        new_config = models.EscapedString.from_value('new_config')
        plugin.raw_config = new_config
        assert plugin.raw_config is new_config
        assert self.print_model(plugin) == 'plugin  "name"    "new_config"'

    def test_set_config(self) -> None:
        plugin = self.parser.parse('plugin  "name"    "config"', models.Plugin)
        plugin.config = 'new_config'
        assert self.print_model(plugin) == 'plugin  "name"    "new_config"'

    def test_remove_raw_config(self) -> None:
        plugin = self.parser.parse('plugin  "name"    "config"', models.Plugin)
        plugin.raw_config = None
        assert plugin.raw_config is None
        assert self.print_model(plugin) == 'plugin  "name"'

    def test_remove_config(self) -> None:
        plugin = self.parser.parse('plugin  "name"    "config"', models.Plugin)
        plugin.config = None
        assert self.print_model(plugin) == 'plugin  "name"'

    def test_noop_remove_raw_config(self) -> None:
        plugin = self.parser.parse('plugin  "name"', models.Plugin)
        plugin.raw_config = None
        assert plugin.raw_config is None
        assert self.print_model(plugin) == 'plugin  "name"'

    def test_noop_remove_config(self) -> None:
        plugin = self.parser.parse('plugin  "name"', models.Plugin)
        plugin.config = None
        assert self.print_model(plugin) == 'plugin  "name"'

    def test_create_raw_config(self) -> None:
        plugin = self.parser.parse('plugin  "name"', models.Plugin)
        new_config = models.EscapedString.from_value('new_config')
        plugin.raw_config = new_config
        assert plugin.raw_config is new_config
        assert self.print_model(plugin) == 'plugin  "name" "new_config"'

    def test_create_config(self) -> None:
        plugin = self.parser.parse('plugin  "name"', models.Plugin)
        plugin.config = 'new_config'
        assert self.print_model(plugin) == 'plugin  "name" "new_config"'

    def test_from_children_with_config(self) -> None:
        name = models.EscapedString.from_value('foo')
        config = models.EscapedString.from_value('bar')
        plugin = models.Plugin.from_children(name, config)
        assert plugin.raw_name is name
        assert plugin.raw_config is config
        assert self.print_model(plugin) == 'plugin "foo" "bar"'
        self.check_consistency(plugin)

    def test_from_children_without_config(self) -> None:
        name = models.EscapedString.from_value('foo')
        plugin = models.Plugin.from_children(name, None)
        assert plugin.raw_name is name
        assert plugin.raw_config is None
        assert self.print_model(plugin) == 'plugin "foo"'
        self.check_consistency(plugin)

    def test_from_value_with_config(self) -> None:
        plugin = models.Plugin.from_value('foo', 'bar')
        assert plugin.raw_name.value == 'foo'
        assert plugin.raw_config and plugin.raw_config.value == 'bar'
        assert self.print_model(plugin) == 'plugin "foo" "bar"'
        self.check_consistency(plugin)

    def test_from_value_without_config(self) -> None:
        plugin = models.Plugin.from_value('foo', None)
        assert plugin.raw_name.value == 'foo'
        assert plugin.raw_config is None
        assert self.print_model(plugin) == 'plugin "foo"'
        self.check_consistency(plugin)
