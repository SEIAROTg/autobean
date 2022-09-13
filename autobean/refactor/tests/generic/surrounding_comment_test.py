import datetime
import decimal
from typing import Optional
import pytest
from autobean.refactor import models
from .. import base


_CLOSE_LEADING = '''\
; foo
; bar
2000-01-01 close Assets:Foo ; baz\
'''
_CLOSE_TRAILING = '''\
2000-01-01 close Assets:Foo ; baz
; qux
; quux\
'''
_CLOSE_BOTH = '''\
; foo
; bar
2000-01-01 close Assets:Foo ; baz
; qux
; quux\
'''
_CLOSE_MULTIPLE = '''\
; aaa
2000-01-01 close Assets:Foo ; baz
; bbb
2000-01-01 close Assets:Bar ; baz
; ccc
'''
_CLOSE_BOTH_SEPARATED = '''\
; foo
; bar

2000-01-01 close Assets:Foo ; baz

; qux
; quux\
'''
_CLOSE_NEITHER = '''\
2000-01-01 close Assets:Foo ; baz\
'''
_CLOSE_BOTH_INDENTED = '''\
2000-01-01 *
    ; aaa
    foo: 1
    ; bbb\
'''
_SET_TESTCASES = [
    (None, None, _CLOSE_NEITHER),
    ('foo\nbar', None, _CLOSE_LEADING),
    (None, 'qux\nquux', _CLOSE_TRAILING),
    ('foo\nbar', 'qux\nquux', _CLOSE_BOTH),
]


class TestSurroundingComment(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text', [_CLOSE_LEADING, _CLOSE_TRAILING, _CLOSE_BOTH, _CLOSE_NEITHER],
    )
    def test_parse_success(self, text: str) -> None:
        self.parser.parse(text, models.Close)

    @pytest.mark.parametrize(
        'leading_comment,trailing_comment,expected_text', _SET_TESTCASES,
    )
    def test_set_raw_comment(self, leading_comment: Optional[str], trailing_comment: Optional[str], expected_text: str) -> None:
        model = self.parser.parse(_CLOSE_NEITHER, models.Close)
        raw_leading_comment = models.BlockComment.from_value(leading_comment) if leading_comment else None
        model.raw_leading_comment = raw_leading_comment
        assert model.raw_leading_comment is raw_leading_comment
        raw_trailing_comment = models.BlockComment.from_value(trailing_comment) if trailing_comment else None
        model.raw_trailing_comment = raw_trailing_comment
        assert model.raw_trailing_comment is raw_trailing_comment
        assert self.print_model(model) == expected_text
        self.check_deepcopy_tree(model)

    @pytest.mark.parametrize(
        'leading_comment,trailing_comment,expected_text', _SET_TESTCASES,
    )
    def test_set_comment(self, leading_comment: Optional[str], trailing_comment: Optional[str], expected_text: str) -> None:
        close = self.parser.parse(_CLOSE_NEITHER, models.Close)
        close.leading_comment = leading_comment
        assert close.leading_comment == leading_comment
        close.trailing_comment = trailing_comment
        assert close.trailing_comment == trailing_comment
        assert self.print_model(close) == expected_text
        self.check_deepcopy_tree(close)

    def test_set_comment_adaptive_indent(self) -> None:
        posting = self.parser.parse('\t\tAssets:Foo  100.00 USD', models.Posting)
        posting.leading_comment = 'foo\nbar'
        posting.trailing_comment = 'baz\nqux'
        assert self.print_model(posting) == '''\
\t\t; foo
\t\t; bar
\t\tAssets:Foo  100.00 USD
\t\t; baz
\t\t; qux\
'''

    @pytest.mark.parametrize(
        'leading_comment,trailing_comment,expected_text', _SET_TESTCASES,
    )
    def test_from_children(self, leading_comment: Optional[str], trailing_comment: Optional[str], expected_text: str) -> None:
        date = models.Date.from_value(datetime.date(2000, 1, 1))
        account = models.Account.from_value('Assets:Foo')
        inline_comment = models.InlineComment.from_value('baz')
        raw_leading_comment = models.BlockComment.from_value(leading_comment) if leading_comment else None
        raw_trailing_comment = models.BlockComment.from_value(trailing_comment) if trailing_comment else None
        close = models.Close.from_children(
            date,
            account,
            inline_comment=inline_comment,
            leading_comment=raw_leading_comment,
            trailing_comment=raw_trailing_comment)
        assert close.raw_leading_comment is raw_leading_comment
        assert close.raw_trailing_comment is raw_trailing_comment
        assert self.print_model(close) == expected_text
        self.check_deepcopy_tree(close)

    @pytest.mark.parametrize(
        'leading_comment,trailing_comment,expected_text', _SET_TESTCASES,
    )
    def test_from_value(self, leading_comment: Optional[str], trailing_comment: Optional[str], expected_text: str) -> None:
        close = models.Close.from_value(
            datetime.date(2000, 1, 1),
            'Assets:Foo',
            inline_comment='baz',
            leading_comment=leading_comment,
            trailing_comment=trailing_comment)
        assert close.leading_comment == leading_comment
        assert close.trailing_comment == trailing_comment
        assert self.print_model(close) == expected_text
        self.check_deepcopy_tree(close)

    def test_claim_leading(self) -> None:
        close = self.parser.parse(_CLOSE_BOTH, models.Close)
        assert close.raw_leading_comment is None
        claimed_comment = close.claim_leading_comment()
        assert claimed_comment is not None
        assert claimed_comment.claimed
        assert self.print_model(close) == _CLOSE_LEADING
        assert close.claim_leading_comment() is claimed_comment  # reclaim should be ok
        assert claimed_comment.claimed

        unclaimed_comment = close.unclaim_leading_comment()
        assert unclaimed_comment is claimed_comment
        assert not unclaimed_comment.claimed
        assert self.print_model(close) == _CLOSE_NEITHER

    def test_claim_leading_already_claimed(self) -> None:
        file = self.parser.parse(_CLOSE_MULTIPLE, models.File)
        close_foo, close_bar = file.directives
        close_foo.claim_trailing_comment()
        with pytest.raises(ValueError, match='already claimed'):
            close_bar.claim_leading_comment()
        close_foo.unclaim_trailing_comment()
        assert close_bar.claim_leading_comment() is not None

    def test_claim_leading_already_claimed_suppressed(self) -> None:
        file = self.parser.parse(_CLOSE_MULTIPLE, models.File)
        close_foo, close_bar = file.directives
        close_foo.claim_trailing_comment()
        assert close_bar.claim_leading_comment(ignore_if_already_claimed=True) is None

    def test_claim_trailing(self) -> None:
        close = self.parser.parse(_CLOSE_BOTH, models.Close)
        assert close.raw_trailing_comment is None
        claimed_comment = close.claim_trailing_comment()
        assert claimed_comment is not None
        assert claimed_comment.claimed
        assert self.print_model(close) == _CLOSE_TRAILING
        assert close.claim_trailing_comment() is claimed_comment  # reclaim should be ok

        unclaimed_comment = close.unclaim_trailing_comment()
        assert unclaimed_comment is claimed_comment
        assert not unclaimed_comment.claimed
        assert self.print_model(close) == _CLOSE_NEITHER

    def test_claim_trailing_already_claimed(self) -> None:
        file = self.parser.parse(_CLOSE_MULTIPLE, models.File)
        close_foo, close_bar = file.directives
        close_bar.claim_leading_comment()
        with pytest.raises(ValueError, match='already claimed'):
            close_foo.claim_trailing_comment()
        close_bar.unclaim_leading_comment()
        assert close_foo.claim_trailing_comment() is not None

    def test_claim_trailing_already_claimed_suppressed(self) -> None:
        file = self.parser.parse(_CLOSE_MULTIPLE, models.File)
        close_foo, close_bar = file.directives
        close_bar.claim_leading_comment()
        assert close_foo.claim_trailing_comment(ignore_if_already_claimed=True) is None

    def test_claim_missing(self) -> None:
        close = self.parser.parse(_CLOSE_NEITHER, models.Close)
        assert close.claim_leading_comment() is None
        assert close.claim_trailing_comment() is None

    def test_claim_separated(self) -> None:
        file = self.parser.parse(_CLOSE_BOTH_SEPARATED, models.File)
        close, = file.directives
        assert close.claim_leading_comment() is None
        assert close.claim_trailing_comment() is None

    def test_claim_move_placeholder(self) -> None:
        file = self.parser.parse(_CLOSE_BOTH_INDENTED, models.File)
        txn, = file.directives
        assert isinstance(txn, models.Transaction)
        meta, = txn.raw_meta
        assert meta.claim_leading_comment() is not None
        assert meta.leading_comment == 'aaa'
        assert meta.claim_trailing_comment() is not None
        assert meta.trailing_comment == 'bbb'
        self.check_disjoint(txn._meta, txn._postings)
        txn.trailing_comment = 'foo'
        assert self.print_model(file) == '''\
2000-01-01 *
    ; aaa
    foo: 1
    ; bbb
; foo\
'''

    def test_claim_move_placeholder_again(self) -> None:
        file = self.parser.parse(_CLOSE_BOTH_INDENTED, models.File)
        txn, = file.directives
        assert isinstance(txn, models.Transaction)
        meta, = txn.raw_meta
        meta_trailing = meta.claim_trailing_comment()
        assert meta_trailing is not None
        posting = models.Posting.from_value(
            'Assets:Foo', decimal.Decimal(100), 'USD')
        txn.postings.append(posting)
        meta.unclaim_trailing_comment()
        posting_leading = posting.claim_leading_comment()
        self.check_disjoint(txn._meta, txn._postings)
        assert posting_leading is meta_trailing
        assert self.print_model(file) == '''\
2000-01-01 *
    ; aaa
    foo: 1
    ; bbb
    Assets:Foo 100 USD\
'''
