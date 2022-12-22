import os.path
from autobean.include import plugin
import autobean.utils.plugin_test_utils as utils


@utils.generate_tests(os.path.dirname(__file__), plugin.IncludePlugin.plugin)
def test() -> None:
    pass


def test_include_option() -> None:
    test_path = os.path.join(os.path.dirname(__file__), 'simple')
    source_path = os.path.join(test_path, 'source.bean')
    external_path = os.path.join(test_path, '_external.bean')
    ledger = utils.load_ledger(source_path)

    # assumptions
    assert not ledger.errors
    assert 'include' in ledger.options
    assert external_path not in ledger.options['include']

    _, errors = utils.apply_plugin(
        plugin.IncludePlugin.plugin, ledger.entries, ledger.options, None)

    assert not errors, errors
    assert external_path in ledger.options['include'], 'included files not added into options["include"]'
