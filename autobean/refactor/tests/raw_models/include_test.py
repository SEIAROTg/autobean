from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models
from autobean.refactor.tests.raw_models import conftest


class TestOption:

    @pytest.mark.parametrize(
        'text,filename', [
            ('include "foo"', 'foo'),
            ('include    "multiple\nlines"', 'multiple\nlines'),
        ],
    )
    def test_parse_success(self, text: str, filename: str, parser: parser_lib.Parser) -> None:
        include = parser.parse(text, raw_models.Include)
        assert include.first_token.raw_text == 'include'
        assert include.raw_filename.value == filename
        assert include.last_token is include.raw_filename

    @pytest.mark.parametrize(
        'text', [
            '    include "foo"',
            'include\n"foo"',
            'include "foo" "bar"',
            'include ',
        ],
    )
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse(text, raw_models.Include)

    def test_set_raw_filename(self, parser: parser_lib.Parser, print_model: conftest.PrintModel) -> None:
        include = parser.parse('include  "filename"', raw_models.Include)
        new_filename = parser.parse_token('"new_filename"', raw_models.EscapedString)
        include.raw_filename = new_filename
        assert include.raw_filename is new_filename
        assert print_model(include) == 'include  "new_filename"'
