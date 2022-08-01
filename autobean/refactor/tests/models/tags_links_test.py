import copy
import datetime
from typing import Iterable, Iterator, Optional, overload
from lark import exceptions
import pytest
from autobean.refactor import models
from autobean.refactor import parser as parser_lib
from . import base

_RAW_INDEXES = (
    0,
    1,
    6,
    -1,
    -7,
    slice(5, None),
    slice(-1, None),
    slice(None, 2),
    slice(1, 3),
    slice(5, 1000),
    slice(-1000, None),
    slice(1000, 2000),
    slice(-2, 2),
    slice(2, -2),
    slice(4, 4),
    slice(-1, 2),
    slice(1, -1, 2),
    slice(5, 1, -2),
    slice(1, -1, -2),
    slice(-2, 0, -2),
    slice(-999, 1000, 2),
    slice(None, None, -1),
)
_TAG_INDEXES = (
    0,
    1,
    3,
    -1,
    -4,
    slice(2, None),
    slice(-1, None),
    slice(None, 2),
    slice(1, 3),
    slice(2, 1000),
    slice(-1000, None),
    slice(1000, 2000),
    slice(-2, 2),
    slice(2, -2),
    slice(3, 3),
    slice(-1, 2),
    slice(1, -1, 2),
    slice(3, 1, -2),
    slice(1, -1, -2),
    slice(-2, 0, -2),
    slice(-999, 1000, 2),
    slice(None, None, -1),
)
_RAW_OOR_INDEXES = (7, -8, 1000, -1000)
_TAG_OOR_INDEXES = (4, -5, 1000, -1000)


def _raw_setitem_ok_cases() -> Iterator[tuple[int | slice, list[models.Tag | models.Link]]]:
    for index in _RAW_INDEXES:
        if isinstance(index, int):
            yield (index, [models.Tag.from_value('xxx')])
        elif isinstance(index, slice):
            l = len(range(7)[index])
            yield (index, [models.Tag.from_value(f'xxx{i}') for i in range(l)])
            if index.step in (None, 1):
                yield (index, [])
                yield (index, [models.Tag.from_value('yyy')])
                yield (index, [models.Tag.from_value(f'zzz{i}') for i in range(l + 1)])
        else:
            assert False


def _raw_setitem_size_mismatch_cases() -> Iterator[tuple[slice, list[models.Tag | models.Link]]]:
    for index in _RAW_INDEXES:
        if isinstance(index, int):
            continue
        assert isinstance(index, slice)
        if index.step in (None, 1):
            continue
        l = len(range(7)[index])
        if l:
            yield (index, [])
        if l > 1:
            yield (index, [models.Tag.from_value('yyy')])
        yield (index, [models.Tag.from_value(f'zzz{i}') for i in range(l + 1)])


def _tag_setitem_ok_cases() -> Iterator[tuple[int | slice, list[str]]]:
    for index in _TAG_INDEXES:
        if isinstance(index, int):
            yield (index, ['xxx'])
        elif isinstance(index, slice):
            l = len(range(4)[index])
            yield (index, [f'xxx{i}' for i in range(l)])
        else:
            assert False


def _tag_setitem_size_mismatch_cases() -> Iterator[tuple[slice, list[str]]]:
    for index in _TAG_INDEXES:
        if isinstance(index, int):
            continue
        assert isinstance(index, slice)
        l = len(range(4)[index])
        if l:
            yield (index, [])
        if l > 1:
            yield (index, ['yyy'])
        yield (index, [f'zzz{i}' for i in range(l + 1)])


@pytest.fixture
def document(parser: parser_lib.Parser) -> models.Document:
    text = '2000-01-01 document Assets:Foo "foo"  #aaa  ^bbb  #ccc ^ddd #eee #fff ^ggg'
    return parser.parse(text, models.Document)


@pytest.fixture
def tags() -> list[str]:
    return ['aaa', 'ccc', 'eee', 'fff']


@pytest.fixture
def tags_links() -> list[models.Tag | models.Link]:
    return [
        models.Tag.from_value('aaa'),
        models.Link.from_value('bbb'),
        models.Tag.from_value('ccc'),
        models.Link.from_value('ddd'),
        models.Tag.from_value('eee'),
        models.Tag.from_value('fff'),
        models.Link.from_value('ggg'),
    ]


@overload
def _extract(tokens: Iterable[models.RawTokenModel]) -> list[str]:
    ...
@overload
def _extract(tokens: models.RawTokenModel) -> str:
    ...
def _extract(tokens: Iterable[models.RawTokenModel] | models.RawTokenModel) -> list[str] | str:
    if isinstance(tokens, models.RawTokenModel):
        return tokens.raw_text
    return [token.raw_text for token in tokens]


class TestTagsLinks(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,tags_links,tags,links', [
            ('2000-01-01 document Assets:Foo "foo"', [], [], []),
            ('2000-01-01 document Assets:Foo "foo" #aaa #bbb', [
                models.Tag.from_value('aaa'), models.Tag.from_value('bbb'),
            ], ['aaa', 'bbb'], []),
            ('2000-01-01 document Assets:Foo "foo" ^aaa ^bbb', [
                models.Link.from_value('aaa'), models.Link.from_value('bbb'),
            ], [], ['aaa', 'bbb']),
            ('2000-01-01 document Assets:Foo "foo"  #aaa  ^bbb  #ccc ^ddd #eee #fff ^ggg', [
                models.Tag.from_value('aaa'),
                models.Link.from_value('bbb'),
                models.Tag.from_value('ccc'),
                models.Link.from_value('ddd'),
                models.Tag.from_value('eee'),
                models.Tag.from_value('fff'),
                models.Link.from_value('ggg'),
            ], ['aaa', 'ccc', 'eee', 'fff'], ['bbb', 'ddd', 'ggg']),
        ],
    )
    def test_parse_success(
            self,
            text: str,
            tags_links: list[models.Tag | models.Link],
            tags: list[str],
            links: list[str],
    ) -> None:
        document = self.parser.parse(text, models.Document)
        assert len(document.raw_tags_links) == len(tags_links)
        assert document.raw_tags_links == tags_links
        for i in range(len(tags_links)):
            assert document.raw_tags_links[i] == tags_links[i]

        assert len(document.tags) == len(tags)
        assert document.tags == tags
        for i in range(len(tags)):
            assert document.tags[i] == tags[i]

        assert len(document.links) == len(links)
        assert document.links == links
        for i in range(len(links)):
            assert document.links[i] == links[i]

        # check wrappers are correctly cached
        assert document.raw_tags_links is document.raw_tags_links
        assert document.tags is document.tags
        assert document.links is document.links

        assert self.print_model(document) == text
        self.check_deepcopy_tree(document)
        self.check_reattach_tree(document)

    @pytest.mark.parametrize(
        'text', [
            '2000-01-01 document Assets:Foo #aaa "foo"',
            '2000-01-01 document Assets:Foo "foo"\n#aaa',
            '2000-01-01 document Assets:Foo "foo"\n    #aaa',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Document)

    @pytest.mark.parametrize(
        'index', _RAW_INDEXES,
    )
    def test_raw_getitem(
            self,
            document: models.Document,
            index: int | slice,
            tags_links: list[models.Tag | models.Link],
    ) -> None:
        assert document.raw_tags_links[index] == tags_links[index]

    @pytest.mark.parametrize(
        'index', _RAW_OOR_INDEXES,
    )
    def test_raw_getitem_oor(self, document: models.Document, index: int) -> None:
        assert len(document.raw_tags_links) == 7
        with pytest.raises(IndexError):
            document.raw_tags_links[index]

    @pytest.mark.parametrize(
        'index', _TAG_INDEXES,
    )
    def test_tag_getitem(self, document: models.Document, index: int | slice, tags: list[str]) -> None:
        assert document.tags[index] == tags[index]

    @pytest.mark.parametrize(
        'index', _TAG_OOR_INDEXES,
    )
    def test_tag_getitem_oor(self, document: models.Document, index: int) -> None:
        assert len(document.tags) == 4
        with pytest.raises(IndexError):
            document.tags[index]

    @pytest.mark.parametrize(
        'index', _RAW_INDEXES,
    )
    def test_raw_delitem(
            self,
            document: models.Document,
            index: int | slice,
            tags_links: list[models.Tag | models.Link],
    ) -> None:
        del document.raw_tags_links[index]
        expected = tags_links.copy()
        del expected[index]
        assert document.raw_tags_links == expected
        text = self.print_model(document)
        for m in expected:
            assert m.raw_text in text
        for m in set(tags_links) - set(expected):
            assert m.raw_text not in text

    @pytest.mark.parametrize(
        'index', _RAW_OOR_INDEXES,
    )
    def test_raw_delitem_oor(self, document: models.Document, index: int) -> None:
        with pytest.raises(IndexError):
            del document.raw_tags_links[index]

    @pytest.mark.parametrize(
        'index', _TAG_INDEXES,
    )
    def test_tag_delitem(self, document: models.Document, index: int | slice, tags: list[str]) -> None:
        del document.tags[index]
        expected = tags.copy()
        del expected[index]
        assert document.tags == expected
        text = self.print_model(document)
        for v in expected:
            assert v in text
        for v in set(tags) - set(expected):
            assert v not in text

    @pytest.mark.parametrize(
        'index', _TAG_OOR_INDEXES,
    )
    def test_tag_delitem_oor(self, document: models.Document, index: int) -> None:
        with pytest.raises(IndexError):
            del document.tags[index]

    @pytest.mark.parametrize(
        'index,repl', _raw_setitem_ok_cases(),
    )
    def test_raw_setitem(
            self,
            document: models.Document,
            index: int | slice,
            repl: list[models.Tag | models.Link],
            tags_links: list[models.Tag | models.Link],
    ) -> None:
        if isinstance(index, int):
            removed = [tags_links[index]]
            document.raw_tags_links[index] = repl[0]
            tags_links[index] = repl[0]
        elif isinstance(index, slice):
            removed = tags_links[index]
            document.raw_tags_links[index] = repl
            tags_links[index] = repl
        else:
            assert False
        assert document.raw_tags_links == tags_links
        text = self.print_model(document)
        for m in removed:
            assert m.raw_text not in text
        for m in repl:
            assert m.raw_text in text

    @pytest.mark.parametrize(
        'index,repl', _raw_setitem_size_mismatch_cases(),
    )
    def test_raw_setitem_size_mismatch(
            self,
            document: models.Document,
            index: slice,
            repl: list[models.Tag | models.Link],
    ) -> None:
        with pytest.raises(ValueError, match='sequence of size'):
            document.raw_tags_links[index] = repl

    @pytest.mark.parametrize(
        'index', _RAW_OOR_INDEXES,
    )
    def test_raw_setitem_oor(self, document: models.Document, index: int) -> None:
        with pytest.raises(IndexError):
            document.raw_tags_links[index] = models.Tag.from_value('xxx')

    @pytest.mark.parametrize(
        'index,repl', _tag_setitem_ok_cases(),
    )
    def test_tag_setitem(
            self,
            document: models.Document,
            index: int | slice,
            repl: list[str],
            tags: list[str],
    ) -> None:
        if isinstance(index, int):
            removed = [tags[index]]
            document.tags[index] = repl[0]
            tags[index] = repl[0]
        elif isinstance(index, slice):
            removed = tags[index]
            document.tags[index] = repl
            tags[index] = repl
        else:
            assert False
        assert document.tags == tags
        text = self.print_model(document)
        for v in removed:
            assert v not in text
        for v in repl:
            assert v in text

    @pytest.mark.parametrize(
        'index,repl', _tag_setitem_size_mismatch_cases(),
    )
    def test_tag_setitem_size_mismatch(
            self,
            document: models.Document,
            index: slice,
            repl: list[str],
    ) -> None:
        with pytest.raises(ValueError, match='sequence of size'):
            document.tags[index] = repl

    @pytest.mark.parametrize(
        'index', _TAG_OOR_INDEXES,
    )
    def test_tag_setitem_oor(self, document: models.Document, index: int) -> None:
        with pytest.raises(IndexError):
            document.tags[index] = 'xxx'

    def test_raw_contains(
            self,
            document: models.Document,
            tags_links: list[models.Tag | models.Link],
    ) -> None:
        for m in tags_links:
            assert m in document.raw_tags_links
        assert models.Tag.from_value('xxx') not in document.raw_tags_links
        assert models.Link.from_value('aaa') not in document.raw_tags_links

    def test_tag_contains(self, document: models.Document, tags: list[str]) -> None:
        for v in tags:
            assert v in document.tags
        not_expected = ['bbb', 'ddd', 'ggg']
        for v in not_expected:
            assert v not in document.tags

    @pytest.mark.parametrize(
        'index', [0, 1, 6, 7, -1, -7, -8, 1000, -1000],
    )
    def test_raw_insert(
            self,
            document: models.Document,
            index: int,
            tags_links: list[models.Tag | models.Link],
    ) -> None:
        document.raw_tags_links.insert(index, models.Link.from_value('xxx'))
        tags_links.insert(index, models.Link.from_value('xxx'))
        assert document.raw_tags_links == tags_links
        text = self.print_model(document)
        for m in tags_links:
            assert m.raw_text in text

    @pytest.mark.parametrize(
        'index', [0, 1, 3, 4, -1, -4, -5, 1000, -1000],
    )
    def test_tag_insert(self, document: models.Document, index: int, tags: list[str]) -> None:
        document.tags.insert(index, 'xxx')
        tags.insert(index, 'xxx')
        assert document.tags == tags
        text = self.print_model(document)
        for v in tags:
            assert v in text

    @pytest.mark.parametrize(
        'index', [0, 1, 6, -1, -7, None],
    )
    def test_raw_pop(
            self,
            document: models.Document,
            index: Optional[int],
            tags_links: list[models.Tag | models.Link],
    ) -> None:
        if index is None:
            actual = document.raw_tags_links.pop()
            expected = tags_links.pop()
        else:
            actual = document.raw_tags_links.pop(index)
            expected = tags_links.pop(index)
        assert document.raw_tags_links == tags_links
        assert actual == expected
        assert expected.raw_text not in self.print_model(document)
        document.raw_tags_links.append(actual)  # the token should be usable

    @pytest.mark.parametrize(
        'index', _RAW_OOR_INDEXES,
    )
    def test_raw_pop_oor(self, document: models.Document, index: int) -> None:
        with pytest.raises(IndexError):
            document.raw_tags_links.pop(index)

    def test_raw_pop_empty(self, document: models.Document) -> None:
        document.raw_tags_links.clear()
        with pytest.raises(IndexError):
            document.raw_tags_links.pop()

    @pytest.mark.parametrize(
        'index', [0, 1, 3, -1, -4, None],
    )
    def test_tag_pop(self, document: models.Document, index: Optional[int], tags: list[str]) -> None:
        if index is None:
            actual = document.tags.pop()
            expected = tags.pop()
        else:
            actual = document.tags.pop(index)
            expected = tags.pop(index)
        assert document.tags == tags
        assert actual == expected
        assert actual not in self.print_model(document)

    @pytest.mark.parametrize(
        'index', _TAG_OOR_INDEXES,
    )
    def test_tag_pop_oor(self, document: models.Document, index: int) -> None:
        with pytest.raises(IndexError):
            document.tags.pop(index)

    def test_tag_pop_empty(self, document: models.Document) -> None:
        document.tags.clear()
        with pytest.raises(IndexError):
            document.tags.pop()

    def test_raw_append(self, document: models.Document, tags_links: list[models.Tag | models.Link]) -> None:
        document.raw_tags_links.append(models.Link.from_value('xxx'))
        tags_links.append(models.Link.from_value('xxx'))
        assert document.raw_tags_links == tags_links
        assert self.print_model(document) == '2000-01-01 document Assets:Foo "foo"  #aaa  ^bbb  #ccc ^ddd #eee #fff ^ggg ^xxx'

    def test_tag_append(self, document: models.Document, tags: list[str]) -> None:
        document.tags.append('xxx')
        tags.append('xxx')
        assert document.tags == tags
        assert self.print_model(document) == '2000-01-01 document Assets:Foo "foo"  #aaa  ^bbb  #ccc ^ddd #eee #fff ^ggg #xxx'

    def test_raw_extend(self, document: models.Document, tags_links: list[models.Tag | models.Link]) -> None:
        document.raw_tags_links.extend([
            models.Link.from_value('xxx'),
            models.Tag.from_value('yyy'),
        ])
        tags_links.extend([
            models.Link.from_value('xxx'),
            models.Tag.from_value('yyy'),
        ])
        assert document.raw_tags_links == tags_links
        assert self.print_model(document) == '2000-01-01 document Assets:Foo "foo"  #aaa  ^bbb  #ccc ^ddd #eee #fff ^ggg ^xxx #yyy'

    def test_tag_extend(self, document: models.Document, tags: list[str]) -> None:
        document.tags.extend(['xxx', 'yyy'])
        tags.extend(['xxx', 'yyy'])
        assert document.tags == tags
        assert self.print_model(document) == '2000-01-01 document Assets:Foo "foo"  #aaa  ^bbb  #ccc ^ddd #eee #fff ^ggg #xxx #yyy'

    def test_raw_clear(self, document: models.Document) -> None:
        document.raw_tags_links.clear()
        assert _extract(document.raw_tags_links) == []
        assert self.print_model(document) == '2000-01-01 document Assets:Foo "foo"'

    def test_tag_clear(self, document: models.Document) -> None:
        document.tags.clear()
        assert document.tags == []
        assert self.print_model(document) == '2000-01-01 document Assets:Foo "foo"  ^bbb ^ddd ^ggg'

    def test_raw_copy(self) -> None:
        text1 = '2000-01-01 document Assets:Foo "foo"  #aaa  ^bbb  #ccc ^ddd #eee #fff ^ggg'
        document1 = self.parser.parse(text1, models.Document)
        text2 = '2012-12-12 document Assets:Bar "bar"'
        document2 = self.parser.parse(text2, models.Document)
        with pytest.raises(ValueError, match='reuse node'):
            document2.raw_tags_links = document1.raw_tags_links
        copied = copy.deepcopy(document1.raw_tags_links)
        document2.raw_tags_links = copied
        assert document2.raw_tags_links is copied
        assert document2.raw_tags_links is not document1.raw_tags_links
        assert self.print_model(document2) == '2012-12-12 document Assets:Bar "bar"  #aaa  ^bbb  #ccc ^ddd #eee #fff ^ggg'
        document2.raw_tags_links.append(models.Tag.from_value('hhh'))
        assert self.print_model(document2) == '2012-12-12 document Assets:Bar "bar"  #aaa  ^bbb  #ccc ^ddd #eee #fff ^ggg #hhh'
        assert self.print_model(document1) == text1
        self.check_consistency(document2)

    def test_from_children(self) -> None:
        tags_links: list[models.Tag | models.Link] = [
            models.Tag.from_value('aaa'),
            models.Tag.from_value('bbb'),
            models.Link.from_value('ccc'),
            models.Tag.from_value('ddd'),
        ]
        document = models.Document.from_children(
            date=models.Date.from_value(datetime.date(2000, 1, 1)),
            account=models.Account.from_value('Assets:Foo'),
            filename=models.EscapedString.from_value('foo'),
            tags_links=tags_links,
        )
        assert len(document.raw_tags_links) == 4
        for i in range(4):
            assert document.raw_tags_links[i] is tags_links[i]
        assert self.print_model(document) == '2000-01-01 document Assets:Foo "foo" #aaa #bbb ^ccc #ddd'

    def test_from_value(self) -> None:
        document = models.Document.from_value(
            date=datetime.date(2000, 1, 1),
            account='Assets:Foo',
            filename='foo',
            tags=['aaa', 'bbb'],
            links=['ccc', 'ddd'],
        )
        assert len(document.raw_tags_links) == 4
        assert document.tags == ['aaa', 'bbb']
        assert document.links == ['ccc', 'ddd']
        assert self.print_model(document) == '2000-01-01 document Assets:Foo "foo" #aaa #bbb ^ccc ^ddd'
