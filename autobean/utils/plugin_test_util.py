from typing import List, Optional, Tuple, Dict, Callable
import os.path
import sys
import copy
from beancount import loader
from beancount.core.data import Directive, Transaction
from beancount.parser import printer
from autobean.utils.compare import compare_entries


class PluginTestUtil:
    path: str
    plugin: Callable

    def __init__(self, path: str, plugin: Callable):
        self.path = path
        self.plugin = plugin

    def testcase_path(self, testcase: str, filename: str):
        return os.path.join(self.path, testcase, filename)

    def load_source(self, testcase: str) -> Tuple[List[Directive], Dict]:
        path = self.testcase_path(testcase, 'source.beancount')
        entries, errors, options = loader.load_file(path)
        assert not errors
        return entries, options

    def load_results(self, testcase: str, plugin_option: Optional[str]) -> List[Directive]:
        path = self.testcase_path(testcase, str(plugin_option) + '.beancount')
        entries, errors, options = loader.load_file(path)
        assert not errors
        return entries

    def assert_same_results(self, actuals: List[Directive], expecteds: List[Directive]):
        same, missings1, missings2 = compare_entries(actuals, expecteds)
        for missing in missings1:
            print('Unexpected entry:', file=sys.stderr)
            printer.print_entry(missing, file=sys.stderr)
        for missing in missings2:
            print('Missing entry:', file=sys.stderr)
            printer.print_entry(missing, file=sys.stderr)
        assert same

    def load_errors(self, testcase: str, plugin_option: Optional[str]) -> List[Tuple[str, str, str]]:
        path = self.testcase_path(testcase, str(plugin_option) + '.txt')
        with open(path) as f:
            errors = f.readlines()
        errors = [tuple(error.strip().split(':', 2)) for error in errors]
        return errors

    @staticmethod
    def assert_same_errors(actuals: List, expecteds: List[Tuple[str, str, str]]):
        assert len(actuals) == len(expecteds)
        for actual, expected in zip(actuals, expecteds):
            assert os.path.basename(actual.source['filename']) == expected[0]
            assert actual.source['lineno'] == int(expected[1])
            assert expected[2] in actual.message

    def assert_results(self, testcase: str, plugin_options: Optional[List[Optional[str]]] = None):
        entries, options = self.load_source(testcase)
        if plugin_options is None:
            plugin_options = [None]
        for plugin_option in plugin_options:
            actual, errors = self.invoke_plugin(entries, options, plugin_option)
            assert not errors
            expected = self.load_results(testcase, plugin_option)
            self.assert_same_results(actual, expected)

    def assert_errors(self, testcase: str, plugin_options: Optional[List[Optional[str]]] = None):
        entries, options = self.load_source(testcase)
        if plugin_options is None:
            plugin_options = [None]
        for plugin_option in plugin_options:
            _, actual = self.invoke_plugin(entries, options, plugin_option)
            expected = self.load_errors(testcase, plugin_option)
            self.assert_same_errors(actual, expected)

    def assert_loading_errors(self, testcase: str):
        path = self.testcase_path(testcase, 'source.beancount')
        entries, errors, options = loader.load_file(path)
        expected = self.load_errors(testcase, 'Error')
        self.assert_same_errors(errors, expected)

    def invoke_plugin(self, entries: List[Directive], options: Dict, plugin_option: Optional[str]) -> Tuple[List[Directive], List]:
        entries = copy.deepcopy(entries)
        options = copy.deepcopy(options)
        if plugin_option is None:
            return self.plugin(entries, options)
        return self.plugin(entries, options, plugin_option)
