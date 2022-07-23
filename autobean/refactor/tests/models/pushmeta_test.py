import copy
import decimal
import datetime
from typing import Optional, Type
from lark import exceptions
import pytest
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models
from autobean.refactor.models.raw_models.escaped_string import EscapedString
from . import base


_SimplifiedValue = Optional[raw_models.MetaValue | decimal.Decimal | datetime.date | str | bool]

# (text, key, raw_value, value)
_PushmetaTestcase = tuple[str, str, Optional[raw_models.MetaValue], _SimplifiedValue]
_PUSHMETA_VALID_TESTCASES_FOO: list[_PushmetaTestcase] = [
    ('pushmeta foo:', 'foo', None, None),
    ('pushmeta foo:  "123"', 'foo', raw_models.EscapedString.from_value('123'), '123'),
    ('pushmeta foo:  Assets:Foo', 'foo', raw_models.Account.from_value('Assets:Foo'), raw_models.Account.from_value('Assets:Foo')),
    ('pushmeta foo:  2020-01-01', 'foo', raw_models.Date.from_value(datetime.date(2020, 1, 1)), datetime.date(2020, 1, 1)),
    ('pushmeta foo:  USD', 'foo', raw_models.Currency.from_value('USD'), raw_models.Currency.from_value('USD')),
    ('pushmeta foo:  #foo', 'foo', raw_models.Tag.from_value('foo'), raw_models.Tag.from_value('foo')),
    ('pushmeta foo:  TRUE', 'foo', raw_models.Bool.from_value(True), True),
    ('pushmeta foo:  NULL', 'foo', raw_models.Null.from_raw_text('NULL'), raw_models.Null.from_raw_text('NULL')),
    ('pushmeta foo:  123', 'foo', raw_models.NumberExpr.from_value(decimal.Decimal(123)), decimal.Decimal(123)),
    ('pushmeta foo:  123 USD', 'foo', easy_models.Amount.from_value(decimal.Decimal(123), 'USD'), easy_models.Amount.from_value(decimal.Decimal(123), 'USD')),
]
_PUSHMETA_VALID_TESTCASES_BAR: list[_PushmetaTestcase] = [
    ('pushmeta foo:', 'foo', None, None),
    ('pushmeta foo:  "456"', 'foo', raw_models.EscapedString.from_value('456'), '456'),
    ('pushmeta foo:  Assets:Bar', 'foo', raw_models.Account.from_value('Assets:Bar'), raw_models.Account.from_value('Assets:Bar')),
    ('pushmeta foo:  2012-12-12', 'foo', raw_models.Date.from_value(datetime.date(2012, 12, 12)), datetime.date(2012, 12, 12)),
    ('pushmeta foo:  EUR', 'foo', raw_models.Currency.from_value('EUR'), raw_models.Currency.from_value('EUR')),
    ('pushmeta foo:  #bar', 'foo', raw_models.Tag.from_value('bar'), raw_models.Tag.from_value('bar')),
    ('pushmeta foo:  FALSE', 'foo', raw_models.Bool.from_value(False), False),
    ('pushmeta foo:  NULL', 'foo', raw_models.Null.from_raw_text('NULL'), raw_models.Null.from_raw_text('NULL')),
    ('pushmeta foo:  456', 'foo', raw_models.NumberExpr.from_value(decimal.Decimal(456)), decimal.Decimal(456)),
    ('pushmeta foo:  456 EUR', 'foo', easy_models.Amount.from_value(decimal.Decimal(456), 'EUR'), easy_models.Amount.from_value(decimal.Decimal(456), 'EUR')),
]
_PUSHMETA_VALID_TESTCASES_BAR_ROTATED = [
    *_PUSHMETA_VALID_TESTCASES_BAR[1:],
    _PUSHMETA_VALID_TESTCASES_BAR[0],
]


class TestPushmeta(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,key,raw_value,value', _PUSHMETA_VALID_TESTCASES_FOO + [
            ('pushmeta\t foo:', 'foo', None, None),
        ],
    )
    def test_parse_success(self, text: str, key: str, raw_value: raw_models.MetaValue, value: _SimplifiedValue) -> None:
        del value  # unused
        pushmeta = self._parser.parse(text, raw_models.Pushmeta)
        assert pushmeta.first_token.raw_text == 'pushmeta'
        assert pushmeta.raw_key.value == key
        assert pushmeta.raw_value == raw_value
        if pushmeta.raw_value is None:
            assert pushmeta.last_token is pushmeta.raw_key
        else:
            assert pushmeta.last_token is pushmeta.raw_value.last_token
        assert self.print_model(pushmeta) == text
        self.check_deepcopy_tree(pushmeta)
        self.check_reattach_tree(pushmeta)

    @pytest.mark.parametrize(
        'text', [
            'pushMeta foo:',
            'pushmeta foo',
            'pushmeta ',
            '    pushmeta foo:',
            'pushmeta foo: ^foo',
            'pushmeta foo: *',
            'pushmeta foo: USD 123',
            'pushmeta foo: 123 456',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self._parser.parse(text, raw_models.Pushmeta)

    def test_set_raw_key(self) -> None:
        pushmeta = self._parser.parse('pushmeta  foo:', raw_models.Pushmeta)
        new_key = raw_models.MetaKey.from_value('bar')
        pushmeta.raw_key = new_key
        assert pushmeta.raw_key is new_key
        assert self.print_model(pushmeta) == 'pushmeta  bar:'

    def test_set_key(self) -> None:
        pushmeta = self._parser.parse('pushmeta  foo:', easy_models.Pushmeta)
        assert pushmeta.key == 'foo'
        pushmeta.key = 'bar'
        assert pushmeta.key == 'bar'
        assert self.print_model(pushmeta) == 'pushmeta  bar:'

    @pytest.mark.parametrize(
        'before,after', [
            *zip(_PUSHMETA_VALID_TESTCASES_FOO, _PUSHMETA_VALID_TESTCASES_BAR),
            *zip(_PUSHMETA_VALID_TESTCASES_FOO, _PUSHMETA_VALID_TESTCASES_BAR_ROTATED),
        ]
    )
    def test_set_raw_value(self, before: _PushmetaTestcase, after: _PushmetaTestcase) -> None:
        text_before, _, raw_value, _ = before
        text_after, _, expected_raw_value, _ = after
        pushmeta = self._parser.parse(text_before, raw_models.Pushmeta)
        expected = self._parser.parse(text_after, raw_models.Pushmeta)
        new_value = copy.deepcopy(expected.raw_value)
        pushmeta.raw_value = new_value
        assert pushmeta.raw_value is new_value
        assert pushmeta.raw_value == expected_raw_value
        if raw_value is not None:  # whitespaces may not match if value is created
            assert self.print_model(pushmeta) == text_after

    @pytest.mark.parametrize(
        'before,after', [
            *zip(_PUSHMETA_VALID_TESTCASES_FOO, _PUSHMETA_VALID_TESTCASES_BAR),
            *zip(_PUSHMETA_VALID_TESTCASES_FOO, _PUSHMETA_VALID_TESTCASES_BAR_ROTATED),
        ]
    )
    def test_set_value(self, before: _PushmetaTestcase, after: _PushmetaTestcase) -> None:
        text_before, _, _, value = before
        text_after, _, _, expected_value = after
        pushmeta = self._parser.parse(text_before, easy_models.Pushmeta)
        assert pushmeta.value == value
        expected = self._parser.parse(text_after, easy_models.Pushmeta)
        pushmeta.value = copy.deepcopy(expected.value)
        assert pushmeta.raw_value == expected.raw_value
        assert pushmeta.value == expected_value
        if value is not None:  # whitespaces may not match if value is created
            assert self.print_model(pushmeta) == text_after

    def test_from_children_with_value(self) -> None:
        pushmeta = raw_models.Pushmeta.from_children(
            raw_models.MetaKey.from_value('foo'),
            raw_models.EscapedString.from_value('bar'),
        )
        assert pushmeta.raw_key.value == 'foo'
        assert pushmeta.raw_value == raw_models.EscapedString.from_value('bar')
        assert self.print_model(pushmeta) == 'pushmeta foo: "bar"'
        self.check_consistency(pushmeta)

    def test_from_children_without_value(self) -> None:
        pushmeta = raw_models.Pushmeta.from_children(raw_models.MetaKey.from_value('foo'))
        assert pushmeta.raw_key.value == 'foo'
        assert pushmeta.raw_value is None
        assert self.print_model(pushmeta) == 'pushmeta foo:'
        self.check_consistency(pushmeta)

    # TODO: get value, set value


class TestPopmeta(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,key', [
            ('popmeta foo:', 'foo'),
            ('popmeta\t foo:', 'foo'),
        ],
    )
    def test_parse_success(self, text: str, key: str) -> None:
        popmeta = self._parser.parse(text, raw_models.Popmeta)
        assert popmeta.first_token.raw_text == 'popmeta'
        assert popmeta.raw_key.value == key
        assert popmeta.last_token is popmeta.raw_key
        self.check_deepcopy_tree(popmeta)
        self.check_reattach_tree(popmeta)

    @pytest.mark.parametrize(
        'text', [
            'popMeta foo:',
            'popmeta foo',
            'popmeta ',
            '    popmeta foo:',
            'popmeta foo: 123',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self._parser.parse(text, raw_models.Popmeta)

    def test_set_raw_key(self) -> None:
        popmeta = self._parser.parse('popmeta  foo:', raw_models.Popmeta)
        new_key = raw_models.MetaKey.from_value('bar')
        popmeta.raw_key = new_key
        assert popmeta.raw_key is new_key
        assert self.print_model(popmeta) == 'popmeta  bar:'

    def test_set_key(self) -> None:
        popmeta = self._parser.parse('popmeta  foo:', easy_models.Popmeta)
        assert popmeta.key == 'foo'
        popmeta.key = 'bar'
        assert popmeta.key == 'bar'
        assert self.print_model(popmeta) == 'popmeta  bar:'

    def test_from_children(self) -> None:
        popmeta = raw_models.Popmeta.from_children(raw_models.MetaKey.from_value('foo'))
        assert popmeta.raw_key.value == 'foo'
        assert self.print_model(popmeta) == 'popmeta foo:'
        self.check_consistency(popmeta)

    def test_from_value(self) -> None:
        popmeta = easy_models.Popmeta.from_value('foo')
        assert popmeta.raw_key.value == 'foo'
        assert self.print_model(popmeta) == 'popmeta foo:'
        self.check_consistency(popmeta)
