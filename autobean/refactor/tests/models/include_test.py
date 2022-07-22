from lark import exceptions
import pytest
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models
from . import base


class TestInclude(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,filename', [
            ('include "foo"', 'foo'),
            ('include    "multiple\nlines"', 'multiple\nlines'),
        ],
    )
    def test_parse_success(self, text: str, filename: str) -> None:
        include = self._parser.parse(text, raw_models.Include)
        assert include.first_token.raw_text == 'include'
        assert include.raw_filename.value == filename
        assert include.last_token is include.raw_filename
        self.check_deepcopy_tree(include)
        self.check_reattach_tree(include)

    @pytest.mark.parametrize(
        'text', [
            '    include "foo"',
            'include\n"foo"',
            'include "foo" "bar"',
            'include ',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self._parser.parse(text, raw_models.Include)

    def test_set_raw_filename(self) -> None:
        include = self._parser.parse('include  "filename"', raw_models.Include)
        new_filename = raw_models.EscapedString.from_value('new_filename')
        include.raw_filename = new_filename
        assert include.raw_filename is new_filename
        assert self.print_model(include) == 'include  "new_filename"'

    def test_set_filename(self) -> None:
        include = self._parser.parse('include  "filename"', easy_models.Include)
        assert include.filename == 'filename'
        include.filename = 'new_filename'
        assert include.filename == 'new_filename'
        assert self.print_model(include) == 'include  "new_filename"'

    def test_from_children(self) -> None:
        filename = raw_models.EscapedString.from_value('filename')
        include = raw_models.Include.from_children(filename)
        assert include.raw_filename is filename
        assert self.print_model(include) == 'include "filename"'
        self.check_consistency(include)

    def test_from_value(self) -> None:
        include = easy_models.Include.from_value('foo')
        assert include.raw_filename.value == 'foo'
        assert self.print_model(include) == 'include "foo"'
        self.check_consistency(include)
