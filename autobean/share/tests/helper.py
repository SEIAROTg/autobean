from typing import List, Optional, Tuple, Dict
import os.path
import sys
import copy
from beancount import loader
from beancount.core.data import Directive, Transaction
from beancount.parser import printer
from autobean.share import share


def testcase_path(testcase: str, filename: str):
    return os.path.join(os.path.dirname(__file__), testcase, filename)


def load_source(testcase: str) -> Tuple[List[Directive], Dict]:
    path = testcase_path(testcase, 'source.beancount')
    entries, errors, options = loader.load_file(path)
    assert not errors
    return entries, options


def load_results(testcase: str, viewpoint: Optional[str]) -> List[Directive]:
    path = testcase_path(testcase, str(viewpoint) + '.beancount')
    entries, errors, options = loader.load_file(path)
    assert not errors
    return entries


def clear_positional_meta(entry: Directive):
    entry.meta.pop('filename', None)
    entry.meta.pop('lineno', None)
    if isinstance(entry, Transaction):
        for posting in entry.postings:
            posting.meta.pop('filename', None)
            posting.meta.pop('lineno', None)


def assert_same_results(actuals: List[Directive], expecteds: List[Directive]):
    assert len(actuals) == len(expecteds)
    for actual, expected in zip(actuals, expecteds):
        clear_positional_meta(actual)
        clear_positional_meta(expected)
        if actual != expected:
            print('Directive mismatch. Expected:', file=sys.stderr)
            printer.print_entry(expected, file=sys.stderr)
            print('Actual:', file=sys.stderr)
            printer.print_entry(actual, file=sys.stderr)
            assert False


def load_errors(testcase: str, viewpoint: Optional[str]) -> List[Tuple[str, str, str]]:
    path = testcase_path(testcase, str(viewpoint) + '.txt')
    with open(path) as f:
        errors = f.readlines()
    errors = [tuple(error.strip().split(':', 2)) for error in errors]
    return errors


def assert_same_errors(actuals: List, expecteds: List[Tuple[str, str, str]]):
    assert len(actuals) == len(expecteds)
    for actual, expected in zip(actuals, expecteds):
        assert os.path.basename(actual.source['filename']) == expected[0]
        assert actual.source['lineno'] == int(expected[1])
        assert expected[2] in actual.message


def assert_results(testcase: str, viewpoints: List[Optional[str]]):
    entries, options = load_source(testcase)

    for viewpoint in viewpoints:
        actual, errors = share(copy.deepcopy(entries), copy.deepcopy(options), viewpoint)
        assert not errors
        expected = load_results(testcase, viewpoint)
        assert_same_results(actual, expected)


def assert_errors(testcase: str, viewpoints: List[Optional[str]]):
    entries, options = load_source(testcase)

    for viewpoint in viewpoints:
        _, actual = share(copy.deepcopy(entries), copy.deepcopy(options), viewpoint)
        expected = load_errors(testcase, viewpoint)
        assert_same_errors(actual, expected)


def assert_loading_errors(testcase: str):
    path = testcase_path(testcase, 'source.beancount')
    entries, errors, options = loader.load_file(path)
    expected = load_errors(testcase, 'Error')
    assert_same_errors(errors, expected)
