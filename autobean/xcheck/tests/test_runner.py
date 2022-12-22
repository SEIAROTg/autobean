import os.path
from autobean.xcheck import plugin
import autobean.utils.plugin_test_utils as utils


@utils.generate_tests(os.path.dirname(__file__), plugin.CrossCheckPlugin.plugin)
def test() -> None:
    pass


def test_include_option() -> None:
    test_path = os.path.join(os.path.dirname(__file__), 'pass')
    source_path = os.path.join(test_path, 'source.bean')
    statement_path = os.path.join(test_path, '_statement.bean')
    ledger = utils.load_ledger(source_path)

    # assumptions
    assert not ledger.errors
    assert 'include' in ledger.options
    assert statement_path not in ledger.options['include']

    _, errors = utils.apply_plugin(plugin.CrossCheckPlugin.plugin, ledger.entries, ledger.options, None)

    assert not errors, errors
    assert statement_path in ledger.options['include'], 'statement files not added into options["include"]'
