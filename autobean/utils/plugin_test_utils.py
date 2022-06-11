import dataclasses
from typing import Any, Callable, NamedTuple, Optional, Union
import os
import sys
import copy
import pytest
from beancount import loader
from beancount.core.data import Directive, Transaction, Open, Close
from beancount.parser import printer
from autobean.utils import error_lib
from autobean.utils.compare import compare_entries


Ledger = tuple[list[Directive], list[error_lib.Error], dict[str, Any]]
NonParameterizedPlugin = Callable[[list[Directive], dict[str, Any]], tuple[list[Directive], list[error_lib.Error]]]
ParameterizedPlugin = Callable[[list[Directive], dict[str, Any], str], tuple[list[Directive], list[error_lib.Error]]]
Plugin = Union[NonParameterizedPlugin, ParameterizedPlugin]

class ExpectedError(NamedTuple):
    filename: str
    lineno: int
    message: str


@dataclasses.dataclass(frozen=True)
class Testcase:
    source: Ledger
    plugin_arg: Optional[str]


@dataclasses.dataclass(frozen=True)
class ResultTestcase(Testcase):
    expected_entries: list[Directive]


@dataclasses.dataclass(frozen=True)
class ErrorTestcase(Testcase):
    expected_errors: list[ExpectedError]


def generate_tests(tests_path: str, plugin: Plugin) -> Callable[[Callable[[], None]], Callable[[Testcase], None]]:
    ids, args = collect_testcases(tests_path)
    def decorator(func: Callable[[], None]) -> Callable[[Testcase], None]:

        def test(testcase: Testcase) -> None:
            source_entries, source_errors, options = testcase.source
            assert not source_errors
            entries, errors = apply_plugin(plugin, source_entries, options, testcase.plugin_arg)
            entries = postprocess(entries)
            if isinstance(testcase, ResultTestcase):
                assert not errors, errors
                assert_same_results(entries, testcase.expected_entries)
            elif isinstance(testcase, ErrorTestcase):
                assert_same_errors(errors, testcase.expected_errors)
            else:
                assert False, f'Unknown testcase type {type(testcase)}'
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
        source_path = os.path.join(full_path, 'source.bean')
        if not os.path.isfile(source_path):
            continue
        source = load_ledger(source_path)
        plugin_args = set()
        for filename in os.listdir(full_path):
            segs = filename.rsplit('.', 2)
            if len(segs) != 2:
                continue
            plugin_arg: Optional[str]
            plugin_arg, expected_type = segs
            if plugin_arg == 'source' or plugin_arg.startswith('.') or plugin_arg.startswith('_'):
                continue
            if plugin_arg == 'None':
                plugin_arg = None
            output_path = os.path.join(full_path, filename)
            testcase: Testcase
            if expected_type == 'bean':  # expect results
                testcase = ResultTestcase(source=copy.deepcopy(source), plugin_arg=plugin_arg, expected_entries=load_ledger(output_path)[0])
            elif expected_type == 'errors':  # expect plugin errors
                testcase = ErrorTestcase(source=copy.deepcopy(source), plugin_arg=plugin_arg, expected_errors=load_expected_errors(output_path))
            else:
                continue
            if plugin_arg in plugin_args:
                raise Exception(f'Multiple output files for "{plugin_arg}" in "{full_path}"')
            plugin_args.add(plugin_arg)
            ids.append(f'{suite} ({plugin_arg})')
            testcases.append(testcase)
    return ids, testcases


def load_ledger(path: str) -> Ledger:
    entries, errors, options = loader.load_file(path)
    return entries, errors, options


def load_expected_errors(path: str) -> list[ExpectedError]:
    with open(path) as f:
        errors = f.readlines()
    rets = []
    for error in errors:
        segs = error.strip().split(':', 2)
        rets.append(ExpectedError(segs[0], int(segs[1]), segs[2]))
    return rets


def assert_same_results(actuals: list[Directive], expecteds: list[Directive]) -> None:
    same, missings1, missings2 = compare_entries(actuals, expecteds)
    for missing in missings1:
        print('Unexpected entry:', file=sys.stderr)
        printer.print_entry(missing, file=sys.stderr)
    for missing in missings2:
        print('Missing entry:', file=sys.stderr)
        printer.print_entry(missing, file=sys.stderr)
    assert same


def assert_same_errors(actuals: list[error_lib.Error], expecteds: list[ExpectedError]) -> None:
    assert len(actuals) == len(expecteds)
    for actual, expected in zip(actuals, expecteds):
        assert os.path.basename(actual.source['filename']) == expected.filename
        assert actual.source['lineno'] == expected.lineno
        assert expected.message in actual.message


def apply_plugin(
        plugin: Callable,
        entries: list[Directive],
        options: dict[str, Any],
        plugin_arg: Optional[str]) -> tuple[list[Directive], list[error_lib.Error]]:

    if plugin_arg is None:
        return plugin(entries, options)
    return plugin(entries, options, plugin_arg)


def postprocess_account(account: str) -> str:
    """Replaces subaccount square brackets with hyphens.

    This is to allow testdata to be parsed normally.
    """
    return account.replace('[', 'TEST--').replace(']', '--')


def postprocess(entries: list[Directive]) -> list[Directive]:
    ret = []
    for entry in entries:
        if isinstance(entry, Transaction):
            postings = [
                posting._replace(
                    account=postprocess_account(posting.account))
                for posting in entry.postings
            ]
            ret.append(entry._replace(postings=postings))
        elif isinstance(entry, Open) or isinstance(entry, Close):
            ret.append(entry._replace(
                account=postprocess_account(entry.account)))
        else:
            ret.append(entry)

    return ret
