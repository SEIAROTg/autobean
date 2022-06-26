from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models


class TestIgnored:

    @pytest.mark.parametrize(
        'text', [
            '; foo',
            ';foo',
            '; 你好!'
            ';',
            '    ; foo',
            'option "" ""    ',
            'option "" "" ; xxx',
            '    \n',
        ],
    )
    def test_parse_success(self, text: str, parser: parser_lib.Parser) -> None:
        parser.parse(text, raw_models.File)

    @pytest.mark.parametrize(
        'text', [
            '"; foo"',
            '    option "" ""',
        ],
    )
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse(text, raw_models.File)
