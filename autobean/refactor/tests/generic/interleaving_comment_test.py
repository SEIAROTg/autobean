import copy
import datetime
import pytest
from autobean.refactor import models
from .. import base

_FILE_FOO = '''\
; comment foo

; comment bar
2000-01-01 open Assets:Foo

; comment baz

2000-01-01 open Assets:Bar

; comment qux\
'''

_FILE_BAR = '''\
; comment foo

2000-01-01 *
    ; comment aaa
    aaa: 1
    ; comment bbb

; comment bar\
'''


class TestInterleavingComment(base.BaseTestModel):

    def test_claim_comment_all(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        assert len(file.raw_directives_with_comments) == 2
        assert len(file.raw_directives) == 2
        assert len(file.directives) == 2
        claimed_comments = file.raw_directives_with_comments.claim_interleaving_comments()
        reclaimed_comments = file.raw_directives_with_comments.claim_interleaving_comments()
        assert [c.value for c in claimed_comments] == [
            'comment foo',
            'comment bar',
            'comment baz',
            'comment qux',
        ]
        self.assert_iterable_same(claimed_comments, reclaimed_comments)
        assert len(file.raw_directives_with_comments) == 6
        assert len(file.raw_directives) == 2
        assert len(file.directives) == 2
        # TODO: assert cmoment value

    def test_unclaim_comment(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        claimed_comments = file.raw_directives_with_comments.claim_interleaving_comments()
        assert len(claimed_comments) == 4
        assert len(file.raw_directives_with_comments) == 6
        unclaimed_comments = file.raw_directives_with_comments.unclaim_interleaving_comments()
        self.assert_iterable_same(claimed_comments, unclaimed_comments)
        assert len(file.raw_directives_with_comments) == 2

    def test_claim_comment_all_but_claimed(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        open_foo, open_bar = file.directives
        assert open_foo.claim_leading_comment() is not None
        claimed_comments = file.raw_directives_with_comments.claim_interleaving_comments()
        assert [c.value for c in claimed_comments] == [
            'comment foo',
            'comment baz',
            'comment qux',
        ]
        assert len(file.raw_directives_with_comments) == 5
        assert len(file.raw_directives) == 2
        assert len(file.directives) == 2

    def test_claim_comment_selectively(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        open_foo, open_bar = file.directives
        leading_comment = open_foo.claim_leading_comment()
        assert leading_comment is not None
        open_foo.unclaim_leading_comment()
        claimed_comments = file.raw_directives_with_comments.claim_interleaving_comments([leading_comment])
        self.assert_iterable_same(claimed_comments, [leading_comment])
        reclaimed_comments = file.raw_directives_with_comments.claim_interleaving_comments([leading_comment])
        self.assert_iterable_same(reclaimed_comments, claimed_comments)
        assert len(file.raw_directives_with_comments) == 3
        assert len(file.raw_directives) == 2
        assert len(file.directives) == 2

    def test_unclaim_comment_selectively(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        claimed_comments = file.raw_directives_with_comments.claim_interleaving_comments()
        assert len(claimed_comments) == 4
        unclaimed_comments = file.raw_directives_with_comments.unclaim_interleaving_comments(claimed_comments[1:3])
        self.assert_iterable_same(unclaimed_comments, claimed_comments[1:3])
        assert len(file.raw_directives_with_comments) == 4
        assert len(file.raw_directives) == 2
        assert len(file.directives) == 2

    def test_claim_comment_selectively_different_token_store(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        open_foo, open_bar = file.directives
        leading_comment = open_foo.claim_leading_comment()
        assert leading_comment is not None
        open_foo.unclaim_leading_comment()
        file2 = self.parser.parse(_FILE_FOO, models.File)
        with pytest.raises(ValueError, match='not found'):
            file2.raw_directives_with_comments.claim_interleaving_comments([leading_comment])
        
    def test_claim_comment_selectively_out_of_scope(self) -> None:
        file = self.parser.parse(_FILE_BAR, models.File)
        file_comments = file.raw_directives_with_comments.claim_interleaving_comments()
        file.raw_directives_with_comments.unclaim_interleaving_comments()
        txn, = file.directives
        assert isinstance(txn, models.Transaction)
        with pytest.raises(ValueError, match='not found'):
            txn.raw_meta_with_comments.claim_interleaving_comments(file_comments)

    def test_claim_comment_selectively_already_claimed(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        open_foo, open_bar = file.directives
        leading_comment = open_foo.claim_leading_comment()
        assert leading_comment is not None
        with pytest.raises(ValueError, match='not found'):
            file.raw_directives_with_comments.claim_interleaving_comments([leading_comment])

    def test_unclaim_comment_selectively_different_token_store(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        claimed_comments = file.raw_directives_with_comments.claim_interleaving_comments()
        file2 = self.parser.parse(_FILE_FOO, models.File)
        file2.raw_directives_with_comments.claim_interleaving_comments()
        with pytest.raises(ValueError, match='not found'):
            file2.raw_directives_with_comments.unclaim_interleaving_comments(claimed_comments)
    
    def test_unclaim_comment_selectively_out_of_scope(self) -> None:
        file = self.parser.parse(_FILE_BAR, models.File)
        file_comments = file.raw_directives_with_comments.claim_interleaving_comments()
        txn, = file.directives
        assert isinstance(txn, models.Transaction)
        with pytest.raises(ValueError, match='not found'):
            txn.raw_meta_with_comments.unclaim_interleaving_comments(file_comments)
    
    def test_unclaim_comment_selectively_already_unalcimed(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        claimed_comments = file.raw_directives_with_comments.claim_interleaving_comments()
        file.raw_directives_with_comments.unclaim_interleaving_comments()
        with pytest.raises(ValueError, match='not found'):
            file.raw_directives_with_comments.unclaim_interleaving_comments(claimed_comments)

    def test_claim_comment_scoped(self) -> None:
        file = self.parser.parse(_FILE_BAR, models.File)
        txn, = file.raw_directives
        assert isinstance(txn, models.Transaction)
        assert len(txn.raw_meta_with_comments) == 1
        assert len(txn.raw_meta) == 1
        assert len(txn.meta) == 1
        claimed_comments = txn.raw_meta_with_comments.claim_interleaving_comments()
        assert [c.value for c in claimed_comments] == [
            'comment aaa',
            'comment bbb',
        ]
        assert len(txn.raw_meta_with_comments) == 3
        assert len(txn.raw_meta) == 1
        assert len(txn.meta) == 1

    def test_claim_comment_outer_stop_early(self) -> None:
        txn = models.Transaction.from_value(
            date=datetime.date(2000, 1, 1),
            payee=None,
            narration=None,
            postings=())
        comment_foo = models.BlockComment.from_value('foo', indent=' ' * 4)
        comment_bar = models.BlockComment.from_value('foo', indent=' ' * 4)
        txn.raw_meta_with_comments.append(comment_foo)
        txn.raw_meta_with_comments.append(comment_bar)
        txn.raw_meta_with_comments.unclaim_interleaving_comments([comment_foo])
        assert not comment_foo.claimed
        assert not txn.raw_postings_with_comments.claim_interleaving_comments()
        txn.raw_meta_with_comments.unclaim_interleaving_comments([comment_bar])
        claimed_comments = txn.raw_postings_with_comments.claim_interleaving_comments()
        self.assert_iterable_same(claimed_comments, [comment_foo, comment_bar])

    def test_claim_comment_move_placeholder(self) -> None:
        file = self.parser.parse(_FILE_BAR, models.File)
        txn, = file.raw_directives
        assert isinstance(txn, models.Transaction)
        claimed_comments = txn.raw_meta_with_comments.claim_interleaving_comments()
        assert len(claimed_comments) == 2
        self.check_disjoint(txn._meta, txn._postings)
        txn.trailing_comment = 'foo'
        assert self.print_model(file) == '''\
; comment foo

2000-01-01 *
    ; comment aaa
    aaa: 1
    ; comment bbb
; foo

; comment bar\
'''

    def test_claim_comment_move_placeholder_again(self) -> None:
        file = self.parser.parse(_FILE_BAR, models.File)
        txn, = file.raw_directives
        assert isinstance(txn, models.Transaction)
        meta_comments = txn.raw_meta_with_comments.claim_interleaving_comments()
        assert len(meta_comments) == 2
        txn.raw_meta_with_comments.unclaim_interleaving_comments()
        posting_comments = txn.raw_postings_with_comments.claim_interleaving_comments()
        self.assert_iterable_same(posting_comments, [meta_comments[-1]])
        self.check_disjoint(txn._meta, txn._postings)

    def test_insert_comment(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        file.raw_directives_with_comments.claim_interleaving_comments()
        comment = models.BlockComment.from_value('aaa\nbbb')
        file.raw_directives_with_comments.insert(4, comment)
        assert len(file.raw_directives_with_comments) == 7
        assert file.raw_directives_with_comments[4] is comment
        assert len(file.raw_directives) == 2
        assert len(file.directives) == 2
        assert self.print_model(file) == '''\
; comment foo

; comment bar
2000-01-01 open Assets:Foo

; comment baz

; aaa
; bbb

2000-01-01 open Assets:Bar

; comment qux\
'''

    def test_remove_comment(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        file.raw_directives_with_comments.claim_interleaving_comments()
        pop_comment = file.raw_directives_with_comments.pop(3)
        assert isinstance(pop_comment, models.BlockComment)
        assert pop_comment.value == 'comment baz'
        assert len(file.raw_directives_with_comments) == 5
        assert len(file.raw_directives) == 2
        assert len(file.directives) == 2
        assert self.print_model(file) == '''\
; comment foo

; comment bar
2000-01-01 open Assets:Foo

2000-01-01 open Assets:Bar

; comment qux\
'''

    def test_from_children(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        file.raw_directives_with_comments.claim_interleaving_comments()
        file = models.File.from_children(copy.deepcopy(file.raw_directives_with_comments[:]))
        assert self.print_model(file) == '''\
; comment foo

; comment bar

2000-01-01 open Assets:Foo

; comment baz

2000-01-01 open Assets:Bar

; comment qux\
'''
