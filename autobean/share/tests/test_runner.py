from autobean.share.tests import helper


def test_simple():
    helper.assert_results('simple', [None, 'Alice', 'Bob'])


def test_relevant_only():
    helper.assert_results('relevant-only', [None, 'Alice', 'Bob'])


def test_metadata_preserve():
    helper.assert_results('metadata-preserve', [None, 'Alice'])


def test_immediate_policy():
    helper.assert_results('immediate-policy', [None, 'Alice', 'Bob'])


def test_named_policy():
    helper.assert_results('named-policy', [None, 'Alice', 'Bob'])


def test_account_policy():
    helper.assert_results('account-policy', [None, 'Alice', 'Bob'])


def test_policy_change():
    helper.assert_results('policy-change', [None, 'Alice', 'Bob'])


def test_account_policy_recursive():
    helper.assert_results('account-policy-recursive', [None, 'Alice', 'Bob'])


def test_account_policy_non_recursive():
    helper.assert_results('account-policy-non-recursive', [None, 'Alice', 'Bob'])


def test_policy_precedence():
    helper.assert_results('policy-precedence', ['Alice', 'Bob'])


def test_buy_for_others():
    helper.assert_results('buy-for-others', [None, 'Alice', 'Bob', 'Charlie'])


def test_proportionate_assertion():
    helper.assert_results('proportionate-assertion', [None, 'Alice'])


def test_proportionate_assertion_fail(): # recursive?
    helper.assert_errors('proportionate-assertion-fail', [None, 'Alice'])


def test_balance_assertion():
    helper.assert_results('balance-assertion', [None, 'Alice'])


def test_check_before_transform():
    helper.assert_loading_errors('check-before-transform')


def test_errors():
    helper.assert_errors('errors', [None, 'Alice', 'Bob'])
