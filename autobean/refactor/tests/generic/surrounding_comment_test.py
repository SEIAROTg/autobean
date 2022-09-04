import datetime
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
_CLOSE_NEITHER = '''\
2000-01-01 close Assets:Foo ; baz\
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
        close = self.parser.parse(_CLOSE_NEITHER, models.Close)
        close.leading_comment = 'foo\nbar'
        comment = close.raw_leading_comment
        assert comment is not None
        assert comment.claimed
        close.unclaim_leading_comment()
        assert not comment.claimed
        assert self.print_model(close) == _CLOSE_NEITHER
        close.claim_leading_comment(comment)
        assert comment.claimed
        close.claim_leading_comment(comment)  # reclaim should be ok
        assert comment.claimed
        assert self.print_model(close) == _CLOSE_LEADING

    def test_claim_leading_already_claimed(self) -> None:
        close = self.parser.parse(_CLOSE_NEITHER, models.Close)
        close.trailing_comment = 'qux\nquux'
        comment = close.raw_trailing_comment
        assert comment is not None
        assert comment.claimed
        with pytest.raises(ValueError, match='already claimed'):
            close.claim_leading_comment(comment)

    def test_claim_leading_already_exists(self) -> None:
        close = self.parser.parse(_CLOSE_NEITHER, models.Close)
        close.leading_comment = 'foo\nbar'
        comment = models.BlockComment.from_value('aaa')
        comment.claimed = False
        close.token_store.insert_before(close.first_token, [comment, models.Newline.from_default()])
        with pytest.raises(ValueError, match='already exists'):
            close.claim_leading_comment(comment)

    def test_claim_leading_token_store_mismatch(self) -> None:
        close_foo = self.parser.parse(_CLOSE_NEITHER, models.Close)
        close_foo.leading_comment = 'foo\nbar'
        comment = close_foo.raw_leading_comment
        assert comment is not None
        close_foo.unclaim_leading_comment()
        close_bar = self.parser.parse(_CLOSE_NEITHER, models.Close)
        with pytest.raises(ValueError, match='same context'):
            close_bar.claim_leading_comment(comment)

    def test_claim_trailing(self) -> None:
        close = self.parser.parse(_CLOSE_NEITHER, models.Close)
        close.trailing_comment = 'qux\nquux'
        comment = close.raw_trailing_comment
        assert comment is not None
        assert comment.claimed
        close.unclaim_trailing_comment()
        assert not comment.claimed
        assert self.print_model(close) == _CLOSE_NEITHER
        close.claim_trailing_comment(comment)
        assert comment.claimed
        close.claim_trailing_comment(comment)  # reclaim should be ok
        assert comment.claimed
        assert self.print_model(close) == _CLOSE_TRAILING

    def test_claim_trailing_already_claimed(self) -> None:
        close = self.parser.parse(_CLOSE_NEITHER, models.Close)
        close.leading_comment = 'foo\nbar'
        comment = close.raw_leading_comment
        assert comment is not None
        with pytest.raises(ValueError, match='already claimed'):
            close.claim_trailing_comment(comment)

    def test_claim_trailing_already_exists(self) -> None:
        close = self.parser.parse(_CLOSE_NEITHER, models.Close)
        close.trailing_comment = 'qux\nquux'
        comment = models.BlockComment.from_value('aaa')
        comment.claimed = False
        close.token_store.insert_after(close.last_token, [models.Newline.from_default(), comment])
        with pytest.raises(ValueError, match='already exists'):
            close.claim_trailing_comment(comment)

    def test_claim_trailing_token_store_mismatch(self) -> None:
        close_foo = self.parser.parse(_CLOSE_NEITHER, models.Close)
        close_foo.trailing_comment = 'qux\nquux'
        comment = close_foo.raw_trailing_comment
        assert comment is not None
        close_foo.unclaim_trailing_comment()
        close_bar = self.parser.parse(_CLOSE_NEITHER, models.Close)
        with pytest.raises(ValueError, match='same context'):
            close_bar.claim_trailing_comment(comment)
