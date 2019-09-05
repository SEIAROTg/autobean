import os.path
import pytest
from autobean.include import plugin
from autobean.utils.plugin_test_util import PluginTestUtil


@pytest.fixture('module')
def util() -> PluginTestUtil:
    return PluginTestUtil(os.path.dirname(__file__), plugin)


def test_simple(util: PluginTestUtil):
    util.assert_results('simple', [None])


def test_no_recursion(util: PluginTestUtil):
    util.assert_results('no-recursion', [None])


def test_errors(util: PluginTestUtil):
    util.assert_errors('errors')
