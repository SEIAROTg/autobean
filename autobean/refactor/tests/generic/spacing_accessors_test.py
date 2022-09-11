from autobean.refactor import models
from .. import base


_N = models.Newline.from_raw_text
_W = models.Whitespace.from_raw_text
_FILE_FOO = f'''\

; foo

2000-01-01  close   Assets:Foo\r
{" " * 4}

 \t
2000-01-01 close Assets:Bar  ; bar
2000-01-01 close Assets:Baz;baz
  ; inside-baz

; qux

2000-01-01 close Assets:Qux

'''

class TestSpacingAccessors(base.BaseTestModel):

    def test_read_file(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        assert file.raw_spacing_before == ()
        assert file.spacing_before == ''
        assert file.raw_spacing_after == ()
        assert file.spacing_after == ''

    def test_read_directive(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        close_foo, close_bar, close_baz, close_qux = file.directives
        assert close_foo.raw_spacing_before == (_N('\n'), _N('\n'))
        assert close_foo.spacing_before == '\n\n'
        assert (
            close_foo.raw_spacing_after
            == close_bar.raw_spacing_before
            == (_N('\r\n'), _W('    '), _N('\n'), _N('\n'), _W(' \t'), _N('\n')))
        assert close_foo.spacing_after == close_bar.spacing_before == '\r\n    \n\n \t\n'
        assert close_bar.raw_spacing_after == close_baz.raw_spacing_before == (_N('\n'),)
        assert close_bar.spacing_after == close_baz.spacing_before == '\n'
        assert close_baz.raw_spacing_after == (_N('\n'), _N('\n'))
        assert close_baz.spacing_after == '\n\n'
    
    def test_read_inline(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        close_foo, close_bar, close_baz, close_qux = file.directives
        assert isinstance(close_foo, models.Close)
        assert isinstance(close_bar, models.Close)
        assert isinstance(close_baz, models.Close)
        assert close_foo.raw_date.raw_spacing_after == (_W(' ' * 2),)
        assert close_foo.raw_date.spacing_after == ' ' * 2
        assert close_foo.raw_account.raw_spacing_before == (_W(' ' * 3),)
        assert close_foo.raw_account.spacing_before == ' ' * 3
        assert close_bar.raw_inline_comment is not None
        assert (
            close_bar.raw_inline_comment.raw_spacing_before
            == close_bar.raw_inline_comment.raw_spacing_before
            == (_W(' ' * 2),))
        assert (
            close_bar.raw_inline_comment.spacing_before
            == close_bar.raw_account.spacing_after
            == ' ' * 2)
        assert close_baz.raw_inline_comment is not None
        assert (
            close_baz.raw_inline_comment.raw_spacing_before
            == close_baz.raw_account.raw_spacing_after
            == ())
        assert (
            close_baz.raw_inline_comment.spacing_before
            == close_baz.raw_account.spacing_after
            == '')

    def test_update_raw(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        close_foo, close_bar, close_baz, close_qux = file.directives
        close_qux.raw_spacing_after = ()
        assert close_qux.raw_spacing_after == ()
        assert close_qux.spacing_after == ''
        new_spacing = (_N('\r\n'), _W(' ' * 4), _N('\n'))
        close_qux.raw_spacing_before = new_spacing
        self.assert_iterable_same(close_qux.raw_spacing_before, new_spacing)
        assert close_qux.spacing_before == '\r\n    \n'
        assert self.print_model(file) == f'''\

; foo

2000-01-01  close   Assets:Foo\r
{" " * 4}

 \t
2000-01-01 close Assets:Bar  ; bar
2000-01-01 close Assets:Baz;baz
  ; inside-baz

; qux\r
{" " * 4}
2000-01-01 close Assets:Qux'''

    def test_update_value(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        close_foo, close_bar, close_baz, close_qux = file.directives
        close_foo.spacing_before = '\n'
        close_foo.spacing_after = '\n'
        assert self.print_model(file) == f'''\

; foo
2000-01-01  close   Assets:Foo
2000-01-01 close Assets:Bar  ; bar
2000-01-01 close Assets:Baz;baz
  ; inside-baz

; qux

2000-01-01 close Assets:Qux

'''
        close_bar.spacing_before = '\r\n\t\r\n'
        assert self.print_model(file) == f'''\

; foo
2000-01-01  close   Assets:Foo\r
\t\r
2000-01-01 close Assets:Bar  ; bar
2000-01-01 close Assets:Baz;baz
  ; inside-baz

; qux

2000-01-01 close Assets:Qux

'''

    def test_update_inline(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        close_foo, close_bar, close_baz, close_qux = file.directives
        assert isinstance(close_bar, models.Close)
        assert isinstance(close_baz, models.Close)
        assert close_bar.raw_inline_comment is not None
        assert close_baz.raw_inline_comment is not None
        close_bar.raw_inline_comment.spacing_before = ''
        close_baz.raw_inline_comment.spacing_before = '\t\t'
        assert close_bar.raw_inline_comment.spacing_before == ''
        assert close_baz.raw_inline_comment.spacing_before == '\t\t'
        assert self.print_model(file) == f'''\

; foo

2000-01-01  close   Assets:Foo\r
{" " * 4}

 \t
2000-01-01 close Assets:Bar; bar
2000-01-01 close Assets:Baz\t\t;baz
  ; inside-baz

; qux

2000-01-01 close Assets:Qux

'''

    def test_update_reuse_token(self) -> None:
        file = self.parser.parse(_FILE_FOO, models.File)
        close_foo, close_bar, close_baz, close_qux = file.directives
        close_foo.raw_spacing_before += (_N('\r\n'),)
        assert close_foo.spacing_before == '\n\n\r\n'
        close_foo.raw_spacing_after = close_foo.raw_spacing_after[:-2]
        assert close_foo.spacing_after == '\r\n    \n\n'
        assert self.print_model(file) == f'''\

; foo

\r
2000-01-01  close   Assets:Foo\r
{" " * 4}

2000-01-01 close Assets:Bar  ; bar
2000-01-01 close Assets:Baz;baz
  ; inside-baz

; qux

2000-01-01 close Assets:Qux

'''
