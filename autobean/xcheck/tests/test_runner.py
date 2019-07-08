import os.path
import pytest
from autobean.xcheck import plugin
from autobean.utils.plugin_test_util import PluginTestUtil


@pytest.fixture('module')
def util() -> PluginTestUtil:
    return PluginTestUtil(os.path.dirname(__file__), plugin)


def test_balance_assertion(util: PluginTestUtil):
    util.assert_errors('balance-assertion')


def test_pass(util: PluginTestUtil):
    util.assert_results('pass')


def test_missing(util: PluginTestUtil):
    util.assert_errors('missing')


def test_unexpected(util: PluginTestUtil):
    util.assert_errors('unexpected')


def test_errors(util: PluginTestUtil):
    util.assert_errors('errors')
