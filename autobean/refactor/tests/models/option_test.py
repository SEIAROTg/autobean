from lark import exceptions
import pytest
from autobean.refactor import models
from . import base


class TestOption(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,key,value', [
            ('option "foo" "bar"', 'foo', 'bar'),
            ('option    "foo"    "multiple\nlines"', 'foo', 'multiple\nlines'),
        ],
    )
    def test_parse_success(self, text: str, key: str, value: str) -> None:
        option = self.parser.parse(text, models.Option)
        assert option.raw_key.value == key
        assert option.raw_value.value == value
        assert self.print_model(option) == text
        self.check_deepcopy_tree(option)
        self.check_reattach_tree(option)

    @pytest.mark.parametrize(
        'text', [
            '    option "foo" "bar"',
            'optIon "foo" "bar"',
            'option "foo"\n"bar"',
            'option "foo" "bar" "baz"',
            'option "foo"',
            'option ',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Option)

    def test_set_raw_key(self) -> None:
        option = self.parser.parse('option  "key"    "value"', models.Option)
        new_key = models.EscapedString.from_value('new_key')
        option.raw_key = new_key
        assert option.raw_key is new_key
        assert self.print_model(option) == 'option  "new_key"    "value"'

    def test_set_key(self) -> None:
        option = self.parser.parse('option  "key"    "value"', models.Option)
        assert option.key == 'key'
        option.key = 'new_key'
        assert option.key == 'new_key'
        assert self.print_model(option) == 'option  "new_key"    "value"'

    def test_set_raw_value(self) -> None:
        option = self.parser.parse('option  "key"    "value"', models.Option)
        new_value = models.EscapedString.from_value('new_value')
        option.raw_value = new_value
        assert option.raw_value is new_value
        assert self.print_model(option) == 'option  "key"    "new_value"'

    def test_set_value(self) -> None:
        option = self.parser.parse('option  "key"    "value"', models.Option)
        assert option.key == 'key'
        option.key = 'new_key'
        assert option.key == 'new_key'
        assert self.print_model(option) == 'option  "new_key"    "value"'

    def test_noop_set_raw_key(self) -> None:
        option = self.parser.parse('option  "key"    "value"', models.Option)
        initial_key = option.raw_key
        option.raw_key = option.raw_key
        assert option.raw_key is initial_key
        assert self.print_model(option) == 'option  "key"    "value"'

    def test_reuse_active_token(self) -> None:
        option = self.parser.parse('option  "key" "value"', models.Option)
        with pytest.raises(ValueError):
            option.raw_key = option.raw_value

    def test_reuse_inactive_token(self) -> None:
        option = self.parser.parse('option  "key"    "value"', models.Option)
        initial_key = option.raw_key
        option.raw_key = models.EscapedString.from_value('new_key')
        option.raw_key = initial_key
        assert option.raw_key is initial_key
        assert self.print_model(option) == 'option  "key"    "value"'

    def test_from_children(self) -> None:
        key = models.EscapedString.from_value('foo')
        value = models.EscapedString.from_value('bar')
        option = models.Option.from_children(key, value)
        assert option.raw_key is key
        assert option.raw_value is value
        assert self.print_model(option) == 'option "foo" "bar"'
        self.check_consistency(option)

    def test_from_value(self) -> None:
        option = models.Option.from_value('foo', 'bar')
        assert option.raw_key.value == 'foo'
        assert option.raw_value.value == 'bar'
        assert self.print_model(option) == 'option "foo" "bar"'
        self.check_consistency(option)
