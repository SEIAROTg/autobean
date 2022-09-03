import datetime
import itertools
from lark import exceptions
import pytest
from autobean.refactor import models
from .. import base


_FOO_FILE = '''\

; comment before

option "operating_currency" "USD"
include "path"
plugin "foo" "multiple
line
config"
pushtag #foo
poptag #foo
pushmeta foo:
popmeta foo:

; comment

2000-01-01 balance Assets:Foo 12.34 USD
    foo: 123

2000-01-01 close Assets:Foo
    foo: 123

2000-01-01 commodity GBP
    foo: 123

2000-01-01 pad Assets:Foo Assets:Bar
    foo: 123

2000-01-01 event "name" "description"
    foo: 123

2000-01-01 query "name" "query string"
    foo: 123

2000-01-01 price GBP 2.00 USD
    foo: 123

2000-01-01 note Assets:Foo "note"
    foo: 123

2000-01-01 document Assets:Foo "path" #tag ^link
    foo: 123

2000-01-01 open Assets:Foo USD, GBP "STRICT"
    foo: 123

2000-01-01 custom "foo" "bar" 12.34
    foo: 123

2000-01-01 * "payee" "narration" #tag ^link
    Assets:Foo       100.00 USD
    Assets:Bar        50.00 GBP @@

; comment after

'''
_BAR_FILE = '''\
; comment

; ^ empty line
    
; ^ line with only spaces
    ; indented comment

; block
; comment\
'''
_EMPTY_FILE = ''
_SINGLE_COMMENT_FILE = '  ; comment'


class TestFile(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,length', [
            (_FOO_FILE, 19),
            (_BAR_FILE, 0),
            (_EMPTY_FILE, 0),
            (_SINGLE_COMMENT_FILE, 0),
            ('; foo', 0),
            (';foo', 0),
            ('; 你好!', 0),
            (';', 0),
            ('    ; foo', 0),
            ('option "" ""    ', 1),
            ('option "" "" ; xxx', 1),
            ('    \n', 0),
        ]
    )
    def test_parse_success(self, text: str, length: int) -> None:
        file = self.parser.parse(text, models.File)
        assert self.print_model(file) == text
        assert len(file.directives) == length
        self.check_deepcopy_tree(file)

    def test_parse_types(self) -> None:
        file = self.parser.parse(_FOO_FILE, models.File)
        types = [
            models.Option,
            models.Include,
            models.Plugin,
            models.Pushtag,
            models.Poptag,
            models.Pushmeta,
            models.Popmeta,
            models.Balance,
            models.Close,
            models.Commodity,
            models.Pad,
            models.Event,
            models.Query,
            models.Price,
            models.Note,
            models.Document,
            models.Open,
            models.Custom,
            models.Transaction,
        ]
        for directive, expected_type in itertools.zip_longest(file.directives, types):
            assert isinstance(directive, expected_type)

    @pytest.mark.parametrize(
        'text', [
            '"; foo"',
            '    option "" ""',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.File)

    def test_from_children(self) -> None:
        option = models.Option.from_value('foo', 'bar')
        open = models.Open.from_value(datetime.date(2000, 1, 1), 'Assets:Foo')
        file = models.File.from_children([option, open])
        assert len(file.directives) == 2
        assert file.directives[0] is option
        assert file.directives[1] is open
        assert self.print_model(file) == 'option "foo" "bar"\n2000-01-01 open Assets:Foo'

    def test_from_value(self) -> None:
        option = models.Option.from_value('foo', 'bar')
        open = models.Open.from_value(datetime.date(2000, 1, 1), 'Assets:Foo')
        file = models.File.from_value([option, open])
        assert len(file.directives) == 2
        assert file.directives[0] is option
        assert file.directives[1] is open
        assert self.print_model(file) == 'option "foo" "bar"\n2000-01-01 open Assets:Foo'

    def test_comments(self) -> None:
        text = '''\
; comment at the beginning

include "foo.bean"

; comment in the middle

include "bar.bean"

; comment at the end
'''
        file = self.parser.parse(text, models.File)
        assert self.print_model(file) == text
