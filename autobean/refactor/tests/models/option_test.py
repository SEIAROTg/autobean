from lark import exceptions
import pytest
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models
from . import base


class TestOption(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,key,value', [
            ('option "foo" "bar"', 'foo', 'bar'),
            ('option    "foo"    "multiple\nlines"', 'foo', 'multiple\nlines'),
        ],
    )
    def test_parse_success(self, text: str, key: str, value: str) -> None:
        option = self.raw_parser.parse(text, raw_models.Option)
        assert option.first_token.raw_text == 'option'
        assert option.raw_key.value == key
        assert option.raw_value.value == value
        assert option.last_token is option.raw_value
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
            self.raw_parser.parse(text, raw_models.Option)

    def test_set_raw_key(self) -> None:
        option = self.raw_parser.parse('option  "key"    "value"', raw_models.Option)
        new_key = raw_models.EscapedString.from_value('new_key')
        option.raw_key = new_key
        assert option.raw_key is new_key
        assert self.print_model(option) == 'option  "new_key"    "value"'

    def test_set_key(self) -> None:
        option = self.easy_parser.parse('option  "key"    "value"', easy_models.Option)
        assert option.key == 'key'
        option.key = 'new_key'
        assert option.key == 'new_key'
        assert self.print_model(option) == 'option  "new_key"    "value"'

    def test_set_raw_value(self) -> None:
        option = self.raw_parser.parse('option  "key"    "value"', raw_models.Option)
        new_value = raw_models.EscapedString.from_value('new_value')
        option.raw_value = new_value
        assert option.raw_value is new_value
        assert self.print_model(option) == 'option  "key"    "new_value"'

    def test_set_value(self) -> None:
        option = self.easy_parser.parse('option  "key"    "value"', easy_models.Option)
        assert option.key == 'key'
        option.key = 'new_key'
        assert option.key == 'new_key'
        assert self.print_model(option) == 'option  "new_key"    "value"'

    def test_noop_set_raw_key(self) -> None:
        option = self.raw_parser.parse('option  "key"    "value"', raw_models.Option)
        initial_key = option.raw_key
        option.raw_key = option.raw_key
        assert option.raw_key is initial_key
        assert self.print_model(option) == 'option  "key"    "value"'

    def test_reuse_active_token(self) -> None:
        option = self.raw_parser.parse('option  "key" "value"', raw_models.Option)
        with pytest.raises(ValueError):
            option.raw_key = option.raw_value

    def test_reuse_inactive_token(self) -> None:
        option = self.raw_parser.parse('option  "key"    "value"', raw_models.Option)
        initial_key = option.raw_key
        option.raw_key = raw_models.EscapedString.from_value('new_key')
        option.raw_key = initial_key
        assert option.raw_key is initial_key
        assert self.print_model(option) == 'option  "key"    "value"'

    def test_from_children(self) -> None:
        key = raw_models.EscapedString.from_value('foo')
        value = raw_models.EscapedString.from_value('bar')
        option = raw_models.Option.from_children(key, value)
        assert option.raw_key is key
        assert option.raw_value is value
        assert self.print_model(option) == 'option "foo" "bar"'
        self.check_consistency(option)

    def test_from_value(self) -> None:
        option = easy_models.Option.from_value('foo', 'bar')
        assert option.raw_key.value == 'foo'
        assert option.raw_value.value == 'bar'
        assert self.print_model(option) == 'option "foo" "bar"'
        self.check_consistency(option)
        self.check_flavor_consistency(option)
