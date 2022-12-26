import collections
import dataclasses
import io
import re
from typing import Any, Callable, Optional, Union
import os
import copy
import pytest
from beancount import loader
from beancount.core.data import Directive, Transaction, Open, Close
from beancount.parser import printer
from autobean.utils import error_lib
from autobean.utils.compare import compare_entries


NonParameterizedPlugin = Callable[[list[Directive], dict[str, Any]], tuple[list[Directive], list[error_lib.Error]]]
ParameterizedPlugin = Callable[[list[Directive], dict[str, Any], str], tuple[list[Directive], list[error_lib.Error]]]
Plugin = Union[NonParameterizedPlugin, ParameterizedPlugin]
_BRACKET_ESCAPE_REGEX = re.compile(r':TEST--(.*)--$')


@dataclasses.dataclass(frozen=True)
class Ledger:
    entries: list[Directive]
    errors: list[error_lib.Error]
    options: dict[str, Any]


class ExpectedErrors:
    def __init__(self) -> None:
        self.errors = collections.defaultdict[tuple[str, int], list[str]](list)

    def add(self, filename: str, lineno: int, message: str) -> None:
        self.errors[(filename, lineno)].append(message)

    def format(self) -> str:
        return '\n'.join(
            f'{filename}:{lineno}:{message}'
            for (filename, lineno), messages in sorted(self.errors.items())
            for message in sorted(messages)
        )


@dataclasses.dataclass(frozen=True)
class Testcase:
    source: Ledger
    source_expected_errors: ExpectedErrors
    plugin_arg: Optional[str]
    expected_errors: ExpectedErrors
    expected_entries: Optional[list[Directive]]
    

def generate_tests(tests_path: str, plugin: Plugin) -> Callable[[Callable[[], None]], Callable[[Testcase], None]]:
    ids, args = collect_testcases(tests_path)
    def decorator(func: Callable[[], None]) -> Callable[[Testcase], None]:

        def test(testcase: Testcase) -> None:
            assert_same_errors(testcase.source.errors, testcase.source_expected_errors)
            entries, errors = apply_plugin(
                plugin, testcase.source.entries, testcase.source.options, testcase.plugin_arg)
            if testcase.expected_entries is not None:
                assert_same_results(entries, testcase.expected_entries)
            assert_same_errors(errors, testcase.expected_errors)
            func()

        return pytest.mark.parametrize('testcase', args, ids=ids)(test)
    return decorator


def collect_testcases(tests_path: str) -> tuple[list[str], list[Testcase]]:
    ids: list[str] = []
    testcases: list[Testcase] = []
    suites = os.listdir(tests_path)
    for suite in suites:
        full_path = os.path.join(tests_path, suite)
        if not os.path.isdir(full_path) or suite.startswith('.') or suite.startswith('_'):
            continue
        names = set()
        for filename in os.listdir(full_path):
            segs = filename.rsplit('.', 2)
            if len(segs) != 2:
                continue
            names.add(segs[0])
        if 'source' not in names:
            continue
        names.remove('source')
        source, source_expected_errors = load_testcase(full_path, 'source')
        assert source
        for name in names:
            if name.startswith('_'):
                continue
            plugin_arg = name if name != 'None' else None
            expected_ledger, expected_errors = load_testcase(full_path, name)
            ids.append(f'{suite} ({plugin_arg})')
            testcases.append(Testcase(
                source=copy.deepcopy(source),
                source_expected_errors=source_expected_errors,
                plugin_arg=plugin_arg,
                expected_entries=expected_ledger.entries if expected_ledger else None,
                expected_errors=expected_errors))
    return ids, testcases


def load_testcase(path: str, name: str) -> tuple[Optional[Ledger], ExpectedErrors]:
    bean_path = os.path.join(path, f'{name}.bean')
    ledger = load_ledger(bean_path) if os.path.isfile(bean_path) else None
    if ledger:
        ledger = dataclasses.replace(ledger, entries=unescape_entries(ledger.entries))
    errors_path = os.path.join(path, f'{name}.errors')
    errors = load_expected_errors(errors_path) if os.path.isfile(errors_path) else ExpectedErrors()
    return ledger, errors


def load_ledger(path: str) -> Ledger:
    entries, errors, options = loader.load_file(path)
    return Ledger(entries, errors, options)


def load_expected_errors(path: str) -> ExpectedErrors:
    with open(path) as f:
        lines = f.readlines()
    errors = ExpectedErrors()
    for line in lines:
        filename, lineno, message = line.strip().split(':', 2)
        errors.add(filename, int(lineno), message)
    return errors


def assert_same_results(actuals: list[Directive], expecteds: list[Directive]) -> None:
    # string comparison for better error output
    actual_io = io.StringIO()
    printer.print_entries(actuals, file=actual_io)
    expected_io = io.StringIO()
    printer.print_entries(expecteds, file=expected_io)
    assert actual_io.getvalue() == expected_io.getvalue(), "unexpected output"

    # catch potential mismatch that isn't printed
    same, _, _= compare_entries(actuals, expecteds)
    assert same, "unexpected output"


def assert_same_errors(actuals: list[error_lib.Error], expecteds: ExpectedErrors) -> None:
    actual_errors = ExpectedErrors()
    matched_expected_errors = ExpectedErrors()
    unmatched_expected_errors = copy.deepcopy(expecteds)
    for actual in actuals:
        filename = os.path.basename(actual.source['filename'])
        lineno = actual.source['lineno']
        actual_errors.add(filename, lineno, actual.message)

        keywords = unmatched_expected_errors.errors.get((filename, lineno), [])
        for i, keyword in enumerate(keywords):
            if keyword in actual.message:
                matched_expected_errors.add(filename, lineno, actual.message)
                keywords.pop(i)
                break
    for (filename, lineno), keywords in unmatched_expected_errors.errors.items():
        for keyword in keywords:
            matched_expected_errors.add(filename, lineno, f'*{keyword}*')

    assert actual_errors.format() == matched_expected_errors.format(), "unexpected errors"


def apply_plugin(
        plugin: Callable,
        entries: list[Directive],
        options: dict[str, Any],
        plugin_arg: Optional[str]) -> tuple[list[Directive], list[error_lib.Error]]:

    if plugin_arg is None:
        return plugin(entries, options)
    return plugin(entries, options, plugin_arg)


def unescape_account(account: str) -> str:
    """Unescapes square brackets from expected output.

    Expected output was escaped so it could parse.
    """
    return re.sub(_BRACKET_ESCAPE_REGEX, r':[\1]', account)


def unescape_entries(entries: list[Directive]) -> list[Directive]:
    ret = []
    for entry in entries:
        if isinstance(entry, Transaction):
            postings = [
                posting._replace(
                    account=unescape_account(posting.account))
                for posting in entry.postings
            ]
            ret.append(entry._replace(postings=postings))
        elif isinstance(entry, Open) or isinstance(entry, Close):
            ret.append(entry._replace(
                account=unescape_account(entry.account)))
        else:
            ret.append(entry)

    return ret
