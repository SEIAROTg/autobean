from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models


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
