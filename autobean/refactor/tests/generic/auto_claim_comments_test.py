from autobean.refactor import models
from .. import base

_FILE_FOO = '''\
; comment 0

; comment 1
2000-01-01 open Assets:Foo
    ; comment 2
    foo: 1
    ; comment 3
; comment 4

; comment 5

; comment 6
2000-01-01 *
    ; comment 7
    bar: 1
    ; comment 8
    baz: 2
    ; comment 9
    Assets:Foo  100.00 USD
    ; comment 10
    Assets:Bar  -100.00 USD
    ; comment 11
; comment 12

; comment 13\
'''


class TestAutoClaimComments(base.BaseTestModel):

    def test_auto_claim_comments(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        file.auto_claim_comments()

        # all claimed
        for token in file.token_store:
            if isinstance(token, models.BlockComment):
                assert token.claimed

        assert len(file.raw_directives_with_comments) == 5
        c0, open_foo, c5, txn, c13 = file.raw_directives_with_comments
        assert isinstance(c0, models.BlockComment)
        assert c0.value == 'comment 0'
        assert isinstance(c5, models.BlockComment)
        assert c5.value == 'comment 5'
        assert isinstance(c13, models.BlockComment)
        assert c13.value == 'comment 13'
        assert isinstance(open_foo, models.Open)
        assert open_foo.leading_comment == 'comment 1'
        assert open_foo.trailing_comment == 'comment 4'
        assert len(open_foo.raw_meta_with_comments) == 1

        meta_foo, = open_foo.raw_meta
        assert meta_foo.leading_comment == 'comment 2'
        assert meta_foo.trailing_comment == 'comment 3'

        assert isinstance(txn, models.Transaction)
        assert txn.leading_comment == 'comment 6'
        assert txn.trailing_comment == 'comment 12'
        meta_bar, meta_baz = txn.raw_meta
        assert meta_bar.leading_comment == 'comment 7'
        assert meta_bar.trailing_comment is None
        assert meta_baz.leading_comment == 'comment 8'
        assert meta_baz.trailing_comment is None
        posting_foo, posting_bar = txn.raw_postings
        assert posting_foo.leading_comment == 'comment 9'
        assert posting_foo.trailing_comment is None
        assert posting_bar.leading_comment == 'comment 10'
        assert posting_bar.trailing_comment == 'comment 11'
