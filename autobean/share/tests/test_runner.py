import os.path
import pytest
from autobean.share import plugin
from autobean.utils.plugin_test_util import PluginTestUtil


@pytest.fixture('module')
def util() -> PluginTestUtil:
    return PluginTestUtil(os.path.dirname(__file__), plugin)


def test_simple(util: PluginTestUtil):
    util.assert_results('simple', [None, 'Alice', 'Bob'])


def test_relevant_only(util: PluginTestUtil):
    util.assert_results('relevant-only', [None, 'Alice', 'Bob'])


def test_metadata_preserve(util: PluginTestUtil):
    util.assert_results('metadata-preserve', [None, 'Alice'])


def test_immediate_policy(util: PluginTestUtil):
    util.assert_results('immediate-policy', [None, 'Alice', 'Bob'])


def test_named_policy(util: PluginTestUtil):
    util.assert_results('named-policy', [None, 'Alice', 'Bob'])


def test_account_policy(util: PluginTestUtil):
    util.assert_results('account-policy', [None, 'Alice', 'Bob'])


def test_policy_change(util: PluginTestUtil):
    util.assert_results('policy-change', [None, 'Alice', 'Bob'])


def test_account_policy_recursive(util: PluginTestUtil):
    util.assert_results('account-policy-recursive', [None, 'Alice', 'Bob'])


def test_account_policy_non_recursive(util: PluginTestUtil):
    util.assert_results('account-policy-non-recursive', [None, 'Alice', 'Bob'])


def test_policy_precedence(util: PluginTestUtil):
    util.assert_results('policy-precedence', ['Alice', 'Bob'])


def test_buy_for_others(util: PluginTestUtil):
    util.assert_results('buy-for-others', [None, 'Alice', 'Bob', 'Charlie'])


def test_proportionate_assertion(util: PluginTestUtil):
    util.assert_results('proportionate-assertion', [None, 'Alice'])


def test_proportionate_assertion_fail(util: PluginTestUtil): # recursive?
    util.assert_errors('proportionate-assertion-fail', [None, 'Alice'])


def test_balance_assertion(util: PluginTestUtil):
    util.assert_results('balance-assertion', [None, 'Alice'])


def test_check_before_transform(util: PluginTestUtil):
    util.assert_loading_errors('check-before-transform')


def test_include_None(util: PluginTestUtil):
    util.assert_results('include-None', [None, 'Alice'])


def test_include_Alice(util: PluginTestUtil):
    util.assert_results('include-Alice', [None, 'Alice'])


def test_include_with_plugin(util: PluginTestUtil):
    util.assert_results('include-with-plugin', [None, 'Alice'])


def test_errors(util: PluginTestUtil):
    util.assert_errors('errors', [None, 'Alice', 'Bob'])
