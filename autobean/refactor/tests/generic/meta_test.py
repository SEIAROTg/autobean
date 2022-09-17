import datetime
import decimal
import itertools
from lark import exceptions
import pytest
from autobean.refactor import models, parser as parser_lib
from .. import base


_SIMPLE = '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment bar
    bar: "bar-value" ; bar
    ; comment baz
  baz: 123 +  456   ; baz\
'''
_UNINDENTED = '''\
2000-01-01 close Assets:Foo ; foo
foo: "foo-value" ; foo
bar: "bar-value" ; bar
baz: 123 +  456   ; baz\
'''
_WITH_EMPTY_LINE = '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    bar: "bar-value" ; bar

  baz: 123 +  456   ; baz\
'''
_WITH_INDENTED_EMPTY_LINE = f'''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    bar: "bar-value" ; bar
{"    "}
  baz: 123 +  456   ; baz\
'''
_WITH_UNINDENTED_COMMENT = '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    bar: "bar-value" ; bar
; unindented comment
  baz: 123 +  456   ; baz\
'''
_WITH_INDENTED_COMMENT = '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    bar: "bar-value" ; bar
    ; indented comment
  baz: 123 +  456   ; baz\
'''
_ADAPTIVE_INDENT = '''\
2000-01-01 close Assets:Foo ; foo
\tfoo: "foo-value" ; foo
\t; comment bar
\tbar: "bar-value" ; bar
\t; comment baz
\tbaz: 123 +  456   ; baz\
'''
_ADAPTIVE_INDENT_NESTED = '''\
2000-01-01 *
\tfoo: "foo-value" ; foo
  Assets:Foo 100.00 USD
\t\tbar: "foo-value" ; foo\
'''

@pytest.fixture
def simple_close(parser: parser_lib.Parser) -> models.Close:
    return parser.parse(_SIMPLE, models.Close)


class TestMeta(base.BaseTestModel):

    @pytest.mark.parametrize('text', [_SIMPLE, _WITH_INDENTED_COMMENT, _ADAPTIVE_INDENT])
    def test_parse_success(self, text: str) -> None:
        close = self.parser.parse(text, models.Close)

        assert len(close.meta) == 3

        assert close.raw_meta[1] is close.meta[1]
        assert close.meta[1].key == 'bar'
        assert close.meta[1].value == 'bar-value'
        assert close.raw_meta['bar'] is close.raw_meta[1]
        assert close.meta['bar'] == 'bar-value'
        assert self.print_model(close.meta[1]).lstrip() == 'bar: "bar-value" ; bar'

        assert close.raw_meta[2] is close.meta[2]
        assert close.meta[2].key == 'baz'
        assert close.meta[2].value == decimal.Decimal(579)
        assert close.raw_meta['baz'] is close.raw_meta[2]
        assert close.meta['baz'] == decimal.Decimal(579)
        assert self.print_model(close.meta[2]).lstrip() == 'baz: 123 +  456   ; baz'

        assert self.print_model(close) == text

    @pytest.mark.parametrize(
        'text', [_UNINDENTED, _WITH_EMPTY_LINE, _WITH_INDENTED_EMPTY_LINE, _WITH_UNINDENTED_COMMENT],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Close)

    def test_raw_getitem_not_found(self) -> None:
        close = self.parser.parse(_SIMPLE, models.Close)
        with pytest.raises(KeyError):
            close.raw_meta['qux']

    def test_getitem_not_found(self) -> None:
        close = self.parser.parse(_SIMPLE, models.Close)
        with pytest.raises(KeyError):
            close.meta['qux']

    def test_raw_setitem_update_by_index(self, simple_close: models.Close) -> None:
        meta_item = models.MetaItem.from_value('qux', False)
        simple_close.raw_meta[1] = meta_item
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment bar
    qux: FALSE
    ; comment baz
  baz: 123 +  456   ; baz\
'''
        self.check_consistency(simple_close)

    def test_setitem_update_by_index(self, simple_close: models.Close) -> None:
        meta_item = models.MetaItem.from_value('qux', False)
        simple_close.meta[1] = meta_item
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment bar
    qux: FALSE
    ; comment baz
  baz: 123 +  456   ; baz\
'''
        self.check_consistency(simple_close)

    def test_raw_setitem_update_by_key(self, simple_close: models.Close) -> None:
        date = models.Date.from_value(datetime.date(2012, 12, 12))
        simple_close.meta['baz'] = date
        assert simple_close.raw_meta[2].raw_value is date
        assert simple_close.raw_meta['baz'].raw_value is date
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment bar
    bar: "bar-value" ; bar
    ; comment baz
  baz: 2012-12-12   ; baz\
'''
        self.check_consistency(simple_close)

    def test_setitem_update_by_key(self, simple_close: models.Close) -> None:
        simple_close.meta['baz'] = datetime.date(2012, 12, 12)
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment bar
    bar: "bar-value" ; bar
    ; comment baz
  baz: 2012-12-12   ; baz\
'''
        self.check_consistency(simple_close)

    def test_raw_item_append_by_key(self, simple_close: models.Close) -> None:
        meta_item = models.MetaItem.from_value('qux', False)
        simple_close.raw_meta['quux'] = meta_item
        assert simple_close.raw_meta['qux'] is meta_item
        assert 'quux' not in simple_close.raw_meta
        assert simple_close.raw_meta[3] is meta_item
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment bar
    bar: "bar-value" ; bar
    ; comment baz
  baz: 123 +  456   ; baz
    qux: FALSE\
'''
        self.check_consistency(simple_close)

    def test_setitem_append_by_key(self, simple_close: models.Close) -> None:
        simple_close.meta['qux'] = False
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment bar
    bar: "bar-value" ; bar
    ; comment baz
  baz: 123 +  456   ; baz
    qux: FALSE\
'''
        self.check_consistency(simple_close)

    def test_raw_delitem_by_index(self, simple_close: models.Close) -> None:
        del simple_close.raw_meta[1]
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment baz
  baz: 123 +  456   ; baz\
'''

    def test_delitem_by_index(self, simple_close: models.Close) -> None:
        del simple_close.meta[1]
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment baz
  baz: 123 +  456   ; baz\
'''

    def test_raw_delitem_by_key(self, simple_close: models.Close) -> None:
        del simple_close.raw_meta['bar']
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment baz
  baz: 123 +  456   ; baz\
'''

    def test_delitem_by_key(self, simple_close: models.Close) -> None:
        del simple_close.meta['bar']
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment baz
  baz: 123 +  456   ; baz\
'''

    def test_del_first(self, simple_close: models.Close) -> None:
        simple_close.auto_claim_comments()
        del simple_close.raw_meta[0]
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    ; comment bar
    bar: "bar-value" ; bar
    ; comment baz
  baz: 123 +  456   ; baz\
'''

    def test_raw_pop_by_index(self, simple_close: models.Close) -> None:
        got_meta = simple_close.raw_meta[1]
        pop_meta = simple_close.raw_meta.pop(1)
        assert pop_meta is got_meta
        assert self.print_model(pop_meta) == '    bar: "bar-value" ; bar'
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment baz
  baz: 123 +  456   ; baz\
'''
        simple_close.meta.append(pop_meta)
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment baz
  baz: 123 +  456   ; baz
    bar: "bar-value" ; bar\
'''
        self.check_consistency(simple_close)

    def test_pop_by_index(self, simple_close: models.Close) -> None:
        got_meta = simple_close.meta[1]
        pop_meta = simple_close.meta.pop(1)
        assert pop_meta is got_meta
        assert self.print_model(pop_meta) == '    bar: "bar-value" ; bar'
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment baz
  baz: 123 +  456   ; baz\
'''
        simple_close.meta.append(pop_meta)
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment baz
  baz: 123 +  456   ; baz
    bar: "bar-value" ; bar\
'''
        self.check_consistency(simple_close)

    def test_raw_pop_by_key(self, simple_close: models.Close) -> None:
        got_meta = simple_close.raw_meta['bar']
        pop_meta = simple_close.raw_meta.pop('bar')
        assert pop_meta is got_meta
        assert self.print_model(pop_meta) == '    bar: "bar-value" ; bar'
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment baz
  baz: 123 +  456   ; baz\
'''
        simple_close.meta.append(pop_meta)
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment baz
  baz: 123 +  456   ; baz
    bar: "bar-value" ; bar\
'''
        self.check_consistency(simple_close)

    def test_pop_by_key(self) -> None:
        close = self.parser.parse('''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment bar
    bar: Assets:Bar ; bar
    ; comment baz
  baz: 123 +  456   ; baz\
''', models.Close)
        got_meta = close.meta['bar']
        pop_meta = close.meta.pop('bar')
        assert pop_meta == got_meta
        assert pop_meta == models.Account.from_value('Assets:Bar')
        assert self.print_model(close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment baz
  baz: 123 +  456   ; baz\
'''
        close.meta['qux'] = pop_meta
        assert self.print_model(close) == '''\
2000-01-01 close Assets:Foo ; foo
    foo: "foo-value" ; foo
    ; comment baz
  baz: 123 +  456   ; baz
    qux: Assets:Bar\
'''
        self.check_consistency(close)

    def test_move(self, simple_close: models.Close) -> None:
        for _ in range(20):
            meta = simple_close.raw_meta_with_comments.pop()
            simple_close.raw_meta_with_comments.insert(0, meta)
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    bar: "bar-value" ; bar
  baz: 123 +  456   ; baz
    foo: "foo-value" ; foo\
'''
        self.check_consistency(simple_close)

    def test_insert(self, simple_close: models.Close) -> None:
        meta = models.MetaItem.from_value('qux', 'qux-value')
        simple_close.raw_meta.insert(0, meta)
        assert self.print_model(simple_close) == '''\
2000-01-01 close Assets:Foo ; foo
    qux: "qux-value"
    foo: "foo-value" ; foo
    ; comment bar
    bar: "bar-value" ; bar
    ; comment baz
  baz: 123 +  456   ; baz\
'''
        self.check_consistency(simple_close)


    def test_insert_adaptive_indent(self) -> None:
        close = self.parser.parse(_ADAPTIVE_INDENT, models.Close)
        close.meta['last'] = 'last-value'
        assert self.print_model(close) == '''\
2000-01-01 close Assets:Foo ; foo
\tfoo: "foo-value" ; foo
\t; comment bar
\tbar: "bar-value" ; bar
\t; comment baz
\tbaz: 123 +  456   ; baz
\tlast: "last-value"\
'''

    def test_insert_adaptive_indent_nested(self) -> None:
        transaction = self.parser.parse(_ADAPTIVE_INDENT_NESTED, models.Transaction)
        transaction.meta['aaa'] = 'aaa-value'
        transaction.postings[0].meta['bbb'] = 'bbb-value'
        assert self.print_model(transaction) == '''\
2000-01-01 *
\tfoo: "foo-value" ; foo
\taaa: "aaa-value"
  Assets:Foo 100.00 USD
\t\tbar: "foo-value" ; foo
\t\tbbb: "bbb-value"\
'''

    def test_from_children(self) -> None:
        date = models.Date.from_value(datetime.date(2012, 12, 12))
        account = models.Account.from_value('Assets:Foo')
        meta = [
            models.MetaItem.from_value('foo', decimal.Decimal(123)),
            models.MetaItem.from_value('bar', 'bar-value'),
        ]
        close = models.Close.from_children(date, account, meta=meta)
        assert close.raw_date is date
        assert close.raw_account is account
        self.assert_iterable_same(meta, close.meta)
        assert self.print_model(close) == '''\
2012-12-12 close Assets:Foo
    foo: 123
    bar: "bar-value"\
'''

    def test_from_value(self) -> None:
        close = models.Close.from_value(
            datetime.date(2012, 12, 12),
            'Assets:Foo',
            meta={
                'foo': decimal.Decimal(123),
                'bar': 'bar-value',
            },
        )
        assert self.print_model(close) == '''\
2012-12-12 close Assets:Foo
    foo: 123
    bar: "bar-value"\
'''

    def test_raw_dict_views(self, simple_close: models.Close) -> None:
        keys = simple_close.raw_meta.keys() 
        assert list(keys) == ['foo', 'bar', 'baz']
        values = simple_close.raw_meta.values()
        self.assert_iterable_same(values, simple_close.meta)
        items = simple_close.raw_meta.items()
        for actual, expected in itertools.zip_longest(items, simple_close.meta):
            assert actual[0] == expected.key
            assert actual[1] is expected
        simple_close.meta['xxx'] = 'yyy'
        assert len(keys) == len(values) == len(items) == 4

    def test_raw_dict_views_reversed(self, simple_close: models.Close) -> None:
        keys = simple_close.raw_meta.keys() 
        assert list(reversed(keys)) == ['baz', 'bar', 'foo']
        values = simple_close.raw_meta.values()
        self.assert_iterable_same(reversed(values), reversed(simple_close.meta))
        items = simple_close.raw_meta.items()
        for actual, expected in itertools.zip_longest(reversed(items), reversed(simple_close.meta)):
            assert actual[0] == expected.key
            assert actual[1] is expected
        simple_close.meta['xxx'] = 'yyy'
        assert len(keys) == len(values) == len(items) == 4

    def test_dict_views_reversed(self, simple_close: models.Close) -> None:
        keys = simple_close.meta.keys() 
        assert list(reversed(keys)) == ['baz', 'bar', 'foo']
        values = simple_close.meta.values()
        for actual, expected in itertools.zip_longest(reversed(values), reversed(simple_close.meta)):
            if isinstance(actual, models.RawModel):
                assert actual is expected.value
            else:
                assert actual == expected.value
        items = simple_close.meta.items()
        for (actual_key, actual_value), expected in itertools.zip_longest(
                reversed(items), reversed(simple_close.meta)):
            assert actual_key == expected.key
            if isinstance(actual_value, models.RawModel):
                assert actual_value is expected.value
            else:
                assert actual_value == expected.value
        simple_close.meta['xxx'] = 'yyy'
        assert len(keys) == len(values) == len(items) == 4
