import collections
import dataclasses
import io
import re
from typing import Any, Callable, Optional, Union
import os
import copy
import pytest
from beancount import loader
from beancount.core.data import Balance, Directive, Transaction, Open, Close
from beancount.parser import printer
from autobean.utils import error_lib
from autobean.utils.compare import compare_entries


NonParameterizedPlugin = Callable[[list[Directive], dict[str, Any]], tuple[list[Directive], list[error_lib.Error]]]
ParameterizedPlugin = Callable[[list[Directive], dict[str, Any], str], tuple[list[Directive], list[error_lib.Error]]]
Plugin = Union[NonParameterizedPlugin, ParameterizedPlugin]
_BRACKET_TO_ESCAPE_REGEX = re.compile(r':\[(.*?)\]')
_BRACKET_ESCAPED_REGEX = re.compile(r':TEST--(.*?)--$')


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
    all_ids: list[str] = []
    all_testcases: list[Testcase] = []
    suites = os.listdir(tests_path)
    for suite in suites:
        ids, testcases = load_test_suite(tests_path, suite)
        all_ids += ids
        all_testcases += testcases
    return all_ids, all_testcases


def load_test_suite(tests_path: str, suite: str) -> tuple[list[str], list[Testcase]]:
    full_path = os.path.join(tests_path, suite)
    ids = list[str]()
    testcases = list[Testcase]()
    if not os.path.isdir(full_path) or suite.startswith('.') or suite.startswith('_'):
        return [], []
    names = set()
    for filename in os.listdir(full_path):
        segs = filename.rsplit('.', 2)
        if len(segs) != 2:
            continue
        names.add(segs[0])
    if 'source' not in names:
        return [], []
    names.remove('source')
    source, source_expected_errors = load_expected(full_path, 'source')
    assert source
    for name in names:
        if name.startswith('_'):
            continue
        plugin_arg = name if name != 'None' else None
        expected_ledger, expected_errors = load_expected(
            full_path, name, escape_brackets=True)
        ids.append(f'{suite} ({plugin_arg})')
        testcases.append(Testcase(
            source=copy.deepcopy(source),
            source_expected_errors=source_expected_errors,
            plugin_arg=plugin_arg,
            expected_entries=expected_ledger.entries if expected_ledger else None,
            expected_errors=expected_errors))
    return ids, testcases


def load_expected(
        path: str,
        name: str,
        *,
        escape_brackets: bool = False,
) -> tuple[Optional[Ledger], ExpectedErrors]:
    bean_path = os.path.join(path, f'{name}.bean')
    ledger = (
        load_ledger(bean_path, escape_brackets=escape_brackets)
        if os.path.isfile(bean_path) else None)
    errors_path = os.path.join(path, f'{name}.errors')
    errors = load_expected_errors(errors_path) if os.path.isfile(errors_path) else ExpectedErrors()
    return ledger, errors


def load_ledger(path: str, *, escape_brackets: bool = False) -> Ledger:
    if escape_brackets:
        with open(path) as f:
            content = f.read()
        content = _escape_output(content)
        entries, errors, options = loader.load_string(content)
        entries = _unescape_entries(entries)
    else:
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


def _escape_output(output: str) -> str:
    return re.sub(_BRACKET_TO_ESCAPE_REGEX, r':TEST--\1--', output)


def _unescape_account(account: str) -> str:
    """Unescapes square brackets from expected output.

    Expected output was escaped so it could parse.
    """
    return re.sub(_BRACKET_ESCAPED_REGEX, r':[\1]', account)


def _unescape_entries(entries: list[Directive]) -> list[Directive]:
    ret = []
    entries = sorted(entries, key=lambda e: e.meta['lineno'])
    for entry in entries:
        if isinstance(entry, Transaction):
            postings = [
                posting._replace(
                    account=_unescape_account(posting.account))
                for posting in entry.postings
            ]
            postings = sorted(postings, key=lambda p: p.meta['lineno'])
            ret.append(entry._replace(postings=postings))
        elif isinstance(entry, Open | Close | Balance):
            ret.append(entry._replace(
                account=_unescape_account(entry.account)))
        else:
            ret.append(entry)

    return ret


def generate_goldens(path: str, suite: str, plugin: Plugin) -> None:
    _, testcases = load_test_suite(path, suite)
    if not testcases:
        print(f'No testcases found for {suite}.')
    for testcase in testcases:
        entries, errors = apply_plugin(
            plugin, testcase.source.entries, testcase.source.options, testcase.plugin_arg)
        if testcase.expected_entries is not None:
            output_path = os.path.join(path, suite, f'{testcase.plugin_arg}.bean')
            with open(output_path, 'w') as f:
                printer.print_entries(entries, file=f)
            print(f'Generated {output_path}.')
        if errors:
            expected_errors = ExpectedErrors()
            for error in errors:
                expected_errors.add(
                    os.path.basename(error.source['filename']),
                    error.source['lineno'],
                    error.message)
            output_path = os.path.join(path, suite, f'{testcase.plugin_arg}.errors')
            with open(output_path, 'w') as f:
                f.write(expected_errors.format())
            print(f'Generated {output_path}.')
