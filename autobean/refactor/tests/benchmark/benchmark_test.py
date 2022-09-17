import pytest
from pytest_benchmark.fixture import BenchmarkFixture  # type: ignore[import]
from autobean.refactor import parser as parser_lib
from autobean.refactor import models

_FILE_SIMPLE = '''\
2000-01-01 *
    Assets:Foo   100.00 USD
    Assets:Bar  -100.00 USD

'''

_FILE_COMPLEX = '''\
; comment
2000-01-01 * "payee" "narration" #tag-a #tag-b ^link-a
    meta-a: 1
    ; comment
    meta-b: 2
    ; comment
    Assets:Foo       100.00 USD
        ; comment
        meta-c: 3
    Assets:Bar      -100.00 DSU {{}}
; comment

'''


def _parse_file(parser: parser_lib.Parser, text: str) -> models.File:
    return parser.parse(text, models.File)


def _update_comment(file: models.File, index: int) -> None:
    txn = file.raw_directives_with_comments[index]
    assert isinstance(txn, models.Transaction)
    comment = txn.leading_comment
    assert comment is not None
    file.raw_directives[index].leading_comment = comment[::-1]


def _getitem_repeated(file: models.File, filtered: bool) -> models.Directive | models.BlockComment:
    if filtered:
        return file.raw_directives[-1]
    return file.raw_directives_with_comments[-1]


def _insert_meta(file: models.File, index: int) -> None:
    txn = file.raw_directives[index]
    assert isinstance(txn, models.Transaction)
    meta = txn.raw_meta_with_comments.pop(-1)
    txn.raw_meta_with_comments.insert(0, meta)


@pytest.mark.benchmark(group='parse_simple')
@pytest.mark.parametrize('repeat', [1, 10, 100, 1000])
def test_parse_simple(repeat: int, benchmark: BenchmarkFixture, parser: parser_lib.Parser) -> None:
    benchmark(_parse_file, parser, _FILE_SIMPLE * repeat)


@pytest.mark.benchmark(group='parse_complex')
@pytest.mark.parametrize('repeat', [1, 10, 100, 1000])
def test_parse_complex(repeat: int, benchmark: BenchmarkFixture, parser: parser_lib.Parser) -> None:
    benchmark(_parse_file, parser, _FILE_COMPLEX * repeat)


@pytest.mark.benchmark(group='update_end')
@pytest.mark.parametrize('repeat', [1, 10, 100, 1000])
def test_update_end(repeat: int, benchmark: BenchmarkFixture, parser: parser_lib.Parser) -> None:
    file = parser.parse(_FILE_COMPLEX * repeat, models.File)
    file.raw_directives_with_comments[-1].auto_claim_comments()
    benchmark(_update_comment, file, -1)


@pytest.mark.benchmark(group='update_start')
@pytest.mark.parametrize('repeat', [1, 10, 100, 1000])
def test_update_start(repeat: int, benchmark: BenchmarkFixture, parser: parser_lib.Parser) -> None:
    file = parser.parse(_FILE_COMPLEX * repeat, models.File)
    file.raw_directives_with_comments[0].auto_claim_comments()
    benchmark(_update_comment, file, 0)


@pytest.mark.benchmark(group='getitem_repeated')
@pytest.mark.parametrize('repeat', [1, 10, 100, 1000])
@pytest.mark.parametrize('filtered', [True, False])
def test_getitem_repeated(repeat: int, filtered: bool, benchmark: BenchmarkFixture, parser: parser_lib.Parser) -> None:
    file = parser.parse(_FILE_COMPLEX * repeat, models.File)
    benchmark(_getitem_repeated, file, filtered)


@pytest.mark.benchmark(group='insert_meta_end')
@pytest.mark.parametrize('repeat', [1, 10, 100, 1000])
def test_insert_meta_end(repeat: int, benchmark: BenchmarkFixture, parser: parser_lib.Parser) -> None:
    file = parser.parse(_FILE_COMPLEX * repeat, models.File)
    benchmark(_insert_meta, file, -1)


@pytest.mark.benchmark(group='insert_meta_start')
@pytest.mark.parametrize('repeat', [1, 10, 100, 1000])
def test_insert_meta_start(repeat: int, benchmark: BenchmarkFixture, parser: parser_lib.Parser) -> None:
    file = parser.parse(_FILE_COMPLEX * repeat, models.File)
    benchmark(_insert_meta, file, 0)
