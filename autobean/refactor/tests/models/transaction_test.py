import datetime
import decimal
import itertools
from typing import Optional
from lark import exceptions
import pytest
from autobean.refactor import models, parser as parser_lib
from . import base

_MINIMAL = '2000-01-01 *'
_TXN_FLAG = '2000-01-01 txn'
_WARNING_FLAG = '2000-01-01 !'
_NARRATION_ONLY = '2000-01-01 * "foo"'
_PAYEE_NARRATION = '2000-01-01 * "foo" "bar"'
_TAGS_LINKS = '2000-01-01 * "foo" "bar" #tag1 ^link1 #tag2 ^link2'
_META_ONLY = '''\
2000-01-01 *
    aaa1: 123 + 456 ; aaa2
    bbb1: "bbb2" ; bbb3\
'''
_POSTING_ONLY = '''\
2000-01-01 *
    Assets:Foo               100.00 USD
    Assets:Bar              -100.00 USD\
'''
_COMPLEX = '''\
2000-01-01 * "foo" "bar" #baz ^qux ; quux
    aaa1: 123 + 456 ; aaa2
    bbb1: "bbb2" ; bbb3
    Assets:Foo               100.00 USD
        ccc1: "ccc2" ; ccc3
        ddd1: "ddd2" ; ddd3
    Assets:Bar              -100.00 USD
    eee1: "eee2" ; eee3\
'''

_TOO_MANY_STRINGS = '2000-01-01 * "foo" "bar" "baz"'
_MISSING_FLAG = '2000-01-01 "foo"'
_BAD_FLAG = '2000-01-01 x "foo"'
_UNINDENTED_POSTING = '2000-01-01 *\nAssets:Foo 100.00 USD' 
_UNINDENTED_META = '2000-01-01 *\nfoo: 123'


@pytest.fixture
def simple_transaction(parser: parser_lib.Parser) -> models.Transaction:
    return parser.parse(_PAYEE_NARRATION, models.Transaction)


@pytest.fixture
def complex_transaction(parser: parser_lib.Parser) -> models.Transaction:
    return parser.parse(_COMPLEX, models.Transaction)


@pytest.fixture
def tagged_transaction(parser: parser_lib.Parser) -> models.Transaction:
    return parser.parse(_TAGS_LINKS, models.Transaction)


class TestTransaction(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,date,flag,payee,narration,tags,links', [
            (_MINIMAL, datetime.date(2000, 1, 1), '*', None, None, (), ()),
            (_TXN_FLAG, datetime.date(2000, 1, 1), '*', None, None, (), ()),
            (_WARNING_FLAG, datetime.date(2000, 1, 1), '!', None, None, (), ()),
            (_NARRATION_ONLY, datetime.date(2000, 1, 1), '*', None, 'foo', (), ()),
            (_PAYEE_NARRATION, datetime.date(2000, 1, 1), '*', 'foo', 'bar', (), ()),
            (_TAGS_LINKS, datetime.date(2000, 1, 1), '*', 'foo', 'bar', ('tag1', 'tag2'), ('link1', 'link2')),
            (_META_ONLY, datetime.date(2000, 1, 1), '*', None, None, (), ()),
            (_POSTING_ONLY, datetime.date(2000, 1, 1), '*', None, None, (), ()),
            (_COMPLEX, datetime.date(2000, 1, 1), '*', 'foo', 'bar', ('baz',), ('qux',)),
        ],
    )
    def test_parse_success(
            self,
            text: str,
            date: datetime.date,
            flag: str,
            payee: Optional[str],
            narration: Optional[str],
            tags: tuple[str, ...],
            links: tuple[str, ...],
    ) -> None:
        transaction = self.parser.parse(text, models.Transaction)
        assert transaction.raw_date.value == date
        assert transaction.date == date
        assert transaction.raw_flag.value == flag
        assert transaction.flag == flag
        assert transaction.payee == payee
        assert transaction.narration == narration
        assert tuple(transaction.tags) == tags
        assert tuple(transaction.links) == links
        assert self.print_model(transaction) == text
        self.check_deepcopy_tree(transaction)
        self.check_reattach_tree(transaction)

    def test_parse_success_complex(self) -> None:
        transaction = self.parser.parse(_COMPLEX, models.Transaction)
        assert dict(transaction.meta.items()) == {
            'aaa1': 579,
            'bbb1': 'bbb2',
        }
        assert len(transaction.postings) == 2
        assert self.print_model(transaction.postings[0]) == '''\
Assets:Foo               100.00 USD
        ccc1: "ccc2" ; ccc3
        ddd1: "ddd2" ; ddd3\
'''
        assert dict(transaction.postings[0].meta.items()) == {
            'ccc1': 'ccc2',
            'ddd1': 'ddd2',
        }
        assert self.print_model(transaction.postings[1]) == '''\
Assets:Bar              -100.00 USD
    eee1: "eee2" ; eee3\
'''
        assert dict(transaction.postings[1].meta.items()) == {
            'eee1': 'eee2',
        }

    @pytest.mark.parametrize(
        'text', [_TOO_MANY_STRINGS, _MISSING_FLAG, _BAD_FLAG, _UNINDENTED_POSTING, _UNINDENTED_META],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Transaction)

    def test_set_raw_date(self, simple_transaction: models.Transaction) -> None:
        date = models.Date.from_value(datetime.date(2012, 12, 12))
        simple_transaction.raw_date = date
        assert simple_transaction.raw_date is date
        assert simple_transaction.date == datetime.date(2012, 12, 12)
        assert self.print_model(simple_transaction) == '2012-12-12 * "foo" "bar"'

    def test_set_date(self, simple_transaction: models.Transaction) -> None:
        date = datetime.date(2012, 12, 12)
        simple_transaction.date = date
        assert simple_transaction.raw_date.value == date
        assert simple_transaction.date == date
        assert self.print_model(simple_transaction) == '2012-12-12 * "foo" "bar"'

    def test_set_raw_flag(self, simple_transaction: models.Transaction) -> None:
        flag = models.TransactionFlag.from_raw_text('txn')
        simple_transaction.raw_flag = flag
        assert simple_transaction.raw_flag is flag
        assert self.print_model(simple_transaction) == '2000-01-01 txn "foo" "bar"'

    def test_set_flag(self, simple_transaction: models.Transaction) -> None:
        simple_transaction.flag = '!'
        assert simple_transaction.raw_flag.value == '!'
        assert simple_transaction.flag == '!'
        assert self.print_model(simple_transaction) == '2000-01-01 ! "foo" "bar"'

    def test_update_raw_payee(self, simple_transaction: models.Transaction) -> None:
        payee = models.EscapedString.from_value('baz')
        simple_transaction.raw_payee = payee
        assert simple_transaction.raw_payee is payee
        assert simple_transaction.payee == 'baz'
        assert self.print_model(simple_transaction) == '2000-01-01 * "baz" "bar"'

    def test_update_payee(self, simple_transaction: models.Transaction) -> None:
        simple_transaction.payee = 'baz'
        assert simple_transaction.payee == 'baz'
        assert self.print_model(simple_transaction) == '2000-01-01 * "baz" "bar"'

    def test_remove_raw_payee(self, simple_transaction: models.Transaction) -> None:
        simple_transaction.raw_payee = None
        assert simple_transaction.raw_payee is None
        assert simple_transaction.payee is None
        assert self.print_model(simple_transaction) == '2000-01-01 * "bar"'

    def test_remove_payee(self, simple_transaction: models.Transaction) -> None:
        simple_transaction.payee = None
        assert simple_transaction.raw_payee is None
        assert simple_transaction.payee is None
        assert self.print_model(simple_transaction) == '2000-01-01 * "bar"'

    def test_create_raw_payee_with_narration(self) -> None:
        transaction = self.parser.parse('2000-01-01 * "foo"', models.Transaction)
        payee = models.EscapedString.from_value('bar')
        transaction.raw_payee = payee
        assert transaction.raw_payee is payee
        assert transaction.payee == 'bar'
        assert self.print_model(transaction) == '2000-01-01 * "bar" "foo"'

    def test_create_payee_with_narration(self) -> None:
        transaction = self.parser.parse('2000-01-01 * "foo"', models.Transaction)
        transaction.payee = 'bar'
        assert transaction.payee == 'bar'
        assert self.print_model(transaction) == '2000-01-01 * "bar" "foo"'

    def test_create_raw_payee_without_narration(self) -> None:
        transaction = self.parser.parse('2000-01-01 *', models.Transaction)
        payee = models.EscapedString.from_value('foo')
        transaction.raw_payee = payee
        assert transaction.raw_payee is payee
        assert transaction.payee == 'foo'
        assert self.print_model(transaction) == '2000-01-01 * "foo" ""'

    def test_create_payee_without_narration(self) -> None:
        transaction = self.parser.parse('2000-01-01 *', models.Transaction)
        transaction.payee = 'foo'
        assert transaction.payee == 'foo'
        assert self.print_model(transaction) == '2000-01-01 * "foo" ""'

    def test_update_raw_narration(self, simple_transaction: models.Transaction) -> None:
        narration = models.EscapedString.from_value('baz')
        simple_transaction.raw_narration = narration
        assert simple_transaction.raw_narration is narration
        assert self.print_model(simple_transaction) == '2000-01-01 * "foo" "baz"'

    def test_update_narration(self, simple_transaction: models.Transaction) -> None:
        simple_transaction.narration = 'baz'
        assert simple_transaction.narration == 'baz'
        assert self.print_model(simple_transaction) == '2000-01-01 * "foo" "baz"'

    def test_create_raw_narration(self) -> None:
        transaction = self.parser.parse('2000-01-01 *', models.Transaction)
        narration = models.EscapedString.from_value('foo')
        transaction.raw_narration = narration
        assert transaction.raw_narration is narration
        assert self.print_model(transaction) == '2000-01-01 * "foo"'

    def test_create_narration(self) -> None:
        transaction = self.parser.parse('2000-01-01 *', models.Transaction)
        transaction.narration = 'foo'
        assert transaction.narration == 'foo'
        assert self.print_model(transaction) == '2000-01-01 * "foo"'

    def test_remove_raw_narration_with_payee(self, simple_transaction: models.Transaction) -> None:
        original_narration = simple_transaction.raw_narration
        simple_transaction.raw_narration = None
        assert simple_transaction.raw_narration is not original_narration
        assert simple_transaction.narration == ''
        assert self.print_model(simple_transaction) == '2000-01-01 * "foo" ""'

    def test_remove_narration_with_payee(self, simple_transaction: models.Transaction) -> None:
        simple_transaction.narration = None
        assert simple_transaction.narration == ''
        assert self.print_model(simple_transaction) == '2000-01-01 * "foo" ""'

    def test_remove_raw_narration_without_payee(self) -> None:
        transaction = self.parser.parse('2000-01-01 * "foo"', models.Transaction)
        transaction.raw_narration = None
        assert transaction.raw_narration is None
        assert transaction.narration is None
        assert self.print_model(transaction) == '2000-01-01 *'

    def test_remove_narration_without_payee(self) -> None:
        transaction = self.parser.parse('2000-01-01 * "foo"', models.Transaction)
        transaction.narration = None
        assert transaction.raw_narration is None
        assert transaction.narration is None
        assert self.print_model(transaction) == '2000-01-01 *'

    def test_update_posting(self, complex_transaction: models.Transaction) -> None:
        posting = models.Posting.from_value('Liabilities:Bar', decimal.Decimal('123.45'), 'GBP')
        complex_transaction.postings[0] = posting
        assert complex_transaction.postings[0] is posting
        assert len(complex_transaction.postings) == 2
        assert self.print_model(complex_transaction) == '''\
2000-01-01 * "foo" "bar" #baz ^qux ; quux
    aaa1: 123 + 456 ; aaa2
    bbb1: "bbb2" ; bbb3
    Liabilities:Bar 123.45 GBP
    Assets:Bar              -100.00 USD
    eee1: "eee2" ; eee3\
'''

    def test_insert_posting(self, complex_transaction: models.Transaction) -> None:
        posting = models.Posting.from_value('Liabilities:Bar', decimal.Decimal('123.45'), 'GBP')
        complex_transaction.postings.insert(1, posting)
        assert complex_transaction.postings[1] is posting
        assert len(complex_transaction.postings) == 3
        assert self.print_model(complex_transaction) == '''\
2000-01-01 * "foo" "bar" #baz ^qux ; quux
    aaa1: 123 + 456 ; aaa2
    bbb1: "bbb2" ; bbb3
    Assets:Foo               100.00 USD
        ccc1: "ccc2" ; ccc3
        ddd1: "ddd2" ; ddd3
    Liabilities:Bar 123.45 GBP
    Assets:Bar              -100.00 USD
    eee1: "eee2" ; eee3\
'''

    def test_remove_posting(self, complex_transaction: models.Transaction) -> None:
        del complex_transaction.postings[0]
        assert len(complex_transaction.postings) == 1
        assert self.print_model(complex_transaction) == '''\
2000-01-01 * "foo" "bar" #baz ^qux ; quux
    aaa1: 123 + 456 ; aaa2
    bbb1: "bbb2" ; bbb3
    Assets:Bar              -100.00 USD
    eee1: "eee2" ; eee3\
'''

    def test_update_meta(self, complex_transaction: models.Transaction) -> None:
        meta_item = models.MetaItem.from_value('xxx1', 'xxx2')
        complex_transaction.raw_meta[0] = meta_item
        assert complex_transaction.raw_meta[0] is meta_item
        assert len(complex_transaction.raw_meta) == 2
        assert self.print_model(complex_transaction) == '''\
2000-01-01 * "foo" "bar" #baz ^qux ; quux
    xxx1: "xxx2"
    bbb1: "bbb2" ; bbb3
    Assets:Foo               100.00 USD
        ccc1: "ccc2" ; ccc3
        ddd1: "ddd2" ; ddd3
    Assets:Bar              -100.00 USD
    eee1: "eee2" ; eee3\
'''

    def test_insert_meta(self, complex_transaction: models.Transaction) -> None:
        meta_item = models.MetaItem.from_value('xxx1', 'xxx2')
        complex_transaction.raw_meta.insert(1, meta_item)
        assert complex_transaction.raw_meta[1] is meta_item
        assert len(complex_transaction.raw_meta) == 3
        assert self.print_model(complex_transaction) == '''\
2000-01-01 * "foo" "bar" #baz ^qux ; quux
    aaa1: 123 + 456 ; aaa2
    xxx1: "xxx2"
    bbb1: "bbb2" ; bbb3
    Assets:Foo               100.00 USD
        ccc1: "ccc2" ; ccc3
        ddd1: "ddd2" ; ddd3
    Assets:Bar              -100.00 USD
    eee1: "eee2" ; eee3\
'''

    def test_remove_meta(self, complex_transaction: models.Transaction) -> None:
        del complex_transaction.raw_meta[0]
        assert len(complex_transaction.raw_meta) == 1
        assert self.print_model(complex_transaction) == '''\
2000-01-01 * "foo" "bar" #baz ^qux ; quux
    bbb1: "bbb2" ; bbb3
    Assets:Foo               100.00 USD
        ccc1: "ccc2" ; ccc3
        ddd1: "ddd2" ; ddd3
    Assets:Bar              -100.00 USD
    eee1: "eee2" ; eee3\
'''

    def test_update_tag(self, tagged_transaction: models.Transaction) -> None:
        tagged_transaction.tags[1] = 'xxx'
        assert tagged_transaction.tags[1] == 'xxx'
        assert len(tagged_transaction.tags) == 2
        assert len(tagged_transaction.raw_tags_links) == 4
        assert self.print_model(tagged_transaction) == (
            '2000-01-01 * "foo" "bar" #tag1 ^link1 #xxx ^link2')

    def test_insert_tag(self, tagged_transaction: models.Transaction) -> None:
        tagged_transaction.tags.insert(1, 'xxx')
        assert tagged_transaction.tags[1] == 'xxx'
        assert len(tagged_transaction.tags) == 3
        assert len(tagged_transaction.raw_tags_links) == 5
        assert self.print_model(tagged_transaction) == (
            '2000-01-01 * "foo" "bar" #tag1 ^link1 #xxx #tag2 ^link2')

    def test_remove_tag(self, tagged_transaction: models.Transaction) -> None:
        del tagged_transaction.tags[1]
        assert len(tagged_transaction.tags) == 1
        assert len(tagged_transaction.raw_tags_links) == 3
        assert self.print_model(tagged_transaction) == (
            '2000-01-01 * "foo" "bar" #tag1 ^link1 ^link2')

    def test_update_link(self, tagged_transaction: models.Transaction) -> None:
        tagged_transaction.links[0] = 'xxx'
        assert tagged_transaction.links[0] == 'xxx'
        assert len(tagged_transaction.links) == 2
        assert len(tagged_transaction.raw_tags_links) == 4
        assert self.print_model(tagged_transaction) == (
            '2000-01-01 * "foo" "bar" #tag1 ^xxx #tag2 ^link2')

    def test_insert_link(self, tagged_transaction: models.Transaction) -> None:
        tagged_transaction.links.insert(1, 'xxx')
        assert tagged_transaction.links[1] == 'xxx'
        assert len(tagged_transaction.links) == 3
        assert len(tagged_transaction.raw_tags_links) == 5
        assert self.print_model(tagged_transaction) == (
            '2000-01-01 * "foo" "bar" #tag1 ^link1 #tag2 ^xxx ^link2')

    def test_remove_link(self, tagged_transaction: models.Transaction) -> None:
        del tagged_transaction.links[0]
        assert len(tagged_transaction.links) == 1
        assert len(tagged_transaction.raw_tags_links) == 3
        assert self.print_model(tagged_transaction) == (
            '2000-01-01 * "foo" "bar" #tag1 #tag2 ^link2')

    def test_from_children_payee_only(self) -> None:
        date = models.Date.from_value(datetime.date(2000, 1, 1))
        flag = models.TransactionFlag.from_value('*')
        payee = models.EscapedString.from_value('foo')
        transaction = models.Transaction.from_children(date, flag, payee, None, (), (), ())
        assert transaction.raw_date is date
        assert transaction.raw_flag is flag
        assert transaction.raw_payee is payee
        assert transaction.raw_narration is not None
        assert transaction.narration == ''
        assert self.print_model(transaction) == '2000-01-01 * "foo" ""'

    def test_from_children_narration_only(self) -> None:
        date = models.Date.from_value(datetime.date(2000, 1, 1))
        flag = models.TransactionFlag.from_value('*')
        narration = models.EscapedString.from_value('foo')
        transaction = models.Transaction.from_children(date, flag, None, narration, (), (), ())
        assert transaction.raw_date is date
        assert transaction.raw_flag is flag
        assert transaction.raw_narration is narration
        assert transaction.narration == 'foo'
        assert self.print_model(transaction) == '2000-01-01 * "foo"'

    def test_from_children_payee_narration(self) -> None:
        date = models.Date.from_value(datetime.date(2000, 1, 1))
        flag = models.TransactionFlag.from_value('*')
        payee = models.EscapedString.from_value('foo')
        narration = models.EscapedString.from_value('bar')
        transaction = models.Transaction.from_children(date, flag, payee, narration, (), (), ())
        assert transaction.raw_date is date
        assert transaction.raw_flag is flag
        assert transaction.raw_payee is payee
        assert transaction.raw_narration is narration
        assert self.print_model(transaction) == '2000-01-01 * "foo" "bar"'

    def test_from_children_complex(self) -> None:
        date = models.Date.from_value(datetime.date(2000, 1, 1))
        flag = models.TransactionFlag.from_value('*')
        payee = models.EscapedString.from_value('foo')
        narration = models.EscapedString.from_value('bar')
        tags_links: list[models.Tag | models.Link] = [
            models.Tag.from_value('baz'),
            models.Link.from_value('qux'),
        ]
        meta_items = [
            self.parser.parse('aaa1: 123 + 456 ; aaa2', models.MetaItem),
            self.parser.parse('bbb1: "bbb2" ; bbb3', models.MetaItem),
        ]
        postings = [
            self.parser.parse('''\
Assets:Foo               100.00 USD
        ccc1: "ccc2" ; ccc3
        ddd1: "ddd2" ; ddd3''', models.Posting),
            self.parser.parse('''\
Assets:Bar              -100.00 USD
    eee1: "eee2" ; eee3''', models.Posting)
        ]
        transaction = models.Transaction.from_children(
            date, flag, payee, narration, tags_links, meta_items, postings)
        assert transaction.raw_date is date
        assert transaction.raw_flag is flag
        assert transaction.raw_payee is payee
        assert transaction.raw_narration is narration
        for actual, expected in itertools.zip_longest(tags_links, transaction.raw_tags_links):
            assert actual is expected
        for actual, expected in itertools.zip_longest(meta_items, transaction.raw_meta):
            assert actual is expected
        for actual, expected in itertools.zip_longest(postings, transaction.raw_postings):
            assert actual is expected
        assert self.print_model(transaction) == '''\
2000-01-01 * "foo" "bar" #baz ^qux
    aaa1: 123 + 456 ; aaa2
    bbb1: "bbb2" ; bbb3
    Assets:Foo               100.00 USD
        ccc1: "ccc2" ; ccc3
        ddd1: "ddd2" ; ddd3
    Assets:Bar              -100.00 USD
    eee1: "eee2" ; eee3\
'''

    def test_from_value_payee_only(self) -> None:
        transaction = models.Transaction.from_value(
            date=datetime.date(2000, 1, 1),
            payee='foo',
            narration=None,
            postings=(),
        )
        assert transaction.raw_narration is not None
        assert transaction.flag == '*'
        assert transaction.payee == 'foo'
        assert transaction.narration == ''
        assert self.print_model(transaction) == '2000-01-01 * "foo" ""'

    def test_from_value_narration_only(self) -> None:
        transaction = models.Transaction.from_value(
            date=datetime.date(2000, 1, 1),
            payee=None,
            narration='foo',
            postings=(),
        )
        assert transaction.flag == '*'
        assert transaction.payee is None
        assert transaction.narration == 'foo'
        assert self.print_model(transaction) == '2000-01-01 * "foo"'

    def test_from_value_payee_narration(self) -> None:
        transaction = models.Transaction.from_value(
            date=datetime.date(2000, 1, 1),
            payee='foo',
            narration='bar',
            postings=(),
        )
        assert transaction.flag == '*'
        assert transaction.payee == 'foo'
        assert transaction.narration == 'bar'
        assert self.print_model(transaction) == '2000-01-01 * "foo" "bar"'

    def test_from_value_complex(self) -> None:
        meta_items = [
            self.parser.parse('aaa1: 123 + 456 ; aaa2', models.MetaItem),
            self.parser.parse('bbb1: "bbb2" ; bbb3', models.MetaItem),
        ]
        postings = [
            self.parser.parse('''\
Assets:Foo               100.00 USD
        ccc1: "ccc2" ; ccc3
        ddd1: "ddd2" ; ddd3''', models.Posting),
            self.parser.parse('''\
Assets:Bar              -100.00 USD
    eee1: "eee2" ; eee3''', models.Posting)
        ]
        transaction = models.Transaction.from_value(
            date=datetime.date(2000, 1, 1),
            payee='foo',
            narration='bar',
            tags=('baz',),
            links=('qux',),
            meta={
                'aaa1': self.parser.parse_inline('123 + 456', models.NumberExpr),
                'bbb1': 'bbb2',
            },
            postings=postings,
        )
        assert transaction.date == datetime.date(2000, 1, 1)
        assert transaction.flag == '*'
        assert transaction.payee == 'foo'
        assert transaction.narration == 'bar'
        assert dict(transaction.meta.items()) == {
            'aaa1': decimal.Decimal(579),
            'bbb1': 'bbb2',
        }
        assert self.print_model(transaction) == '''\
2000-01-01 * "foo" "bar" #baz ^qux
    aaa1: 123 + 456
    bbb1: "bbb2"
    Assets:Foo               100.00 USD
        ccc1: "ccc2" ; ccc3
        ddd1: "ddd2" ; ddd3
    Assets:Bar              -100.00 USD
    eee1: "eee2" ; eee3\
'''
