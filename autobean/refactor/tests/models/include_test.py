from lark import exceptions
import pytest
from autobean.refactor import models
from . import base


class TestInclude(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,filename', [
            ('include "foo"', 'foo'),
            ('include    "multiple\nlines"', 'multiple\nlines'),
        ],
    )
    def test_parse_success(self, text: str, filename: str) -> None:
        include = self.parser.parse(text, models.Include)
        assert include.raw_filename.value == filename
        assert self.print_model(include) == text
        self.check_deepcopy_tree(include)
        self.check_reattach_tree(include)

    @pytest.mark.parametrize(
        'text', [
            '    include "foo"',
            'incLude "foo"',
            'include\n"foo"',
            'include "foo" "bar"',
            'include ',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Include)

    def test_set_raw_filename(self) -> None:
        include = self.parser.parse('include  "filename"', models.Include)
        new_filename = models.EscapedString.from_value('new_filename')
        include.raw_filename = new_filename
        assert include.raw_filename is new_filename
        assert self.print_model(include) == 'include  "new_filename"'

    def test_set_filename(self) -> None:
        include = self.parser.parse('include  "filename"', models.Include)
        assert include.filename == 'filename'
        include.filename = 'new_filename'
        assert include.filename == 'new_filename'
        assert self.print_model(include) == 'include  "new_filename"'

    def test_from_children(self) -> None:
        filename = models.EscapedString.from_value('filename')
        include = models.Include.from_children(filename)
        assert include.raw_filename is filename
        assert self.print_model(include) == 'include "filename"'
        self.check_consistency(include)

    def test_from_value(self) -> None:
        include = models.Include.from_value('foo')
        assert include.raw_filename.value == 'foo'
        assert self.print_model(include) == 'include "foo"'
        self.check_consistency(include)
