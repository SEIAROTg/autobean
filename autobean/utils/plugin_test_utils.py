from typing import List, Optional, Tuple, Dict, Callable, Union
import os
import sys
import copy
from collections import namedtuple
import pytest
from beancount import loader
from beancount.core.data import Directive, Transaction, Open, Close
from beancount.parser import printer
from autobean.utils.compare import compare_entries


Ledger = Tuple[List[Directive], List, Dict]
ExpectedError = namedtuple('ExpectedError', 'filename lineno message')
Expected = Union[Ledger, List[ExpectedError]]
TestcaseArg = namedtuple('Testcase', 'source plugin_arg expected_type expected')


def generate_tests(tests_path: str, plugin: Callable):
    ids, args = collect_testcases(tests_path)
    def decorator(func):

        def test(source: Ledger, plugin_arg: Optional[str], expected_type: str, expected: Expected):
            source_entries, source_errors, options = source
            assert not source_errors
            entries, errors = apply_plugin(plugin, source_entries, options, plugin_arg)
            entries = postprocess(entries)
            if expected_type == 'bean':
                assert not errors, errors
                assert_same_results(entries, expected)
            elif expected_type == 'errors':
                assert_same_errors(errors, expected)
            func()

        return pytest.mark.parametrize('source,plugin_arg,expected_type,expected', args, ids=ids)(test)
    return decorator


def collect_testcases(tests_path: str) -> Tuple[List[str], List[TestcaseArg]]:
    ids = []
    args = []
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
            plugin_arg, expected_type = segs
            if plugin_arg == 'source' or plugin_arg.startswith('.') or plugin_arg.startswith('_'):
                continue
            if plugin_arg == 'None':
                plugin_arg = None
            output_path = os.path.join(full_path, filename)
            if expected_type == 'bean':  # expect results
                expected = load_ledger(output_path)[0]
            elif expected_type == 'errors':  # expect plugin errors
                expected = load_expected_errors(output_path)
            else:
                continue
            if plugin_arg in plugin_args:
                raise Exception(f'Multiple output files for "{plugin_arg}" in "{full_path}"')
            plugin_args.add(plugin_arg)
            ids.append(f'{suite} ({plugin_arg})')
            args.append(TestcaseArg(copy.deepcopy(source), plugin_arg, expected_type, expected))
    return ids, args


def load_ledger(path: str) -> Ledger:
    entries, errors, options = loader.load_file(path)
    return entries, errors, options


def load_expected_errors(path: str) -> List[ExpectedError]:
    with open(path) as f:
        errors = f.readlines()
    rets = []
    for error in errors:
        segs = error.strip().split(':', 2)
        rets.append(ExpectedError(segs[0], int(segs[1]), segs[2]))
    return rets


def assert_same_results(actuals: List[Directive], expecteds: List[Directive]):
    same, missings1, missings2 = compare_entries(actuals, expecteds)
    for missing in missings1:
        print('Unexpected entry:', file=sys.stderr)
        printer.print_entry(missing, file=sys.stderr)
    for missing in missings2:
        print('Missing entry:', file=sys.stderr)
        printer.print_entry(missing, file=sys.stderr)
    assert same


def assert_same_errors(actuals: List, expecteds: List[ExpectedError]):
    assert len(actuals) == len(expecteds)
    for actual, expected in zip(actuals, expecteds):
        assert os.path.basename(actual.source['filename']) == expected.filename
        assert actual.source['lineno'] == expected.lineno
        assert expected.message in actual.message


def apply_plugin(
        plugin: Callable,
        entries: List[Directive],
        options: Dict,
        plugin_arg: Optional[str]) -> Tuple[List[Directive], List]:

    if plugin_arg is None:
        return plugin(entries, options)
    return plugin(entries, options, plugin_arg)


def postprocess_account(account: str) -> str:
    """Replaces subaccount square brackets with hyphens.

    This is to allow testdata to be parsed normally.
    """
    return account.replace('[', 'TEST--').replace(']', '--')


def postprocess(entries: List[Directive]) -> List[Directive]:
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


def assert_results(self, testcase: str, plugin_options: Optional[List[Optional[str]]] = None):
    entries, options = self.load_source(testcase)
    if plugin_options is None:
        plugin_options = [None]
    for plugin_option in plugin_options:
        actual, errors = self.invoke_plugin(entries, options, plugin_option)
        assert not errors
        expected = self.load_results(testcase, plugin_option)
        self.assert_same_results(actual, expected)
