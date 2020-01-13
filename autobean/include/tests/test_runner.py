import os.path
from autobean.include import plugin
import autobean.utils.plugin_test_utils as utils


@utils.generate_tests(os.path.dirname(__file__), plugin)
def test():
    pass


def test_include_option():
    test_path = os.path.join(os.path.dirname(__file__), 'simple')
    source_path = os.path.join(test_path, 'source.bean')
    external_path = os.path.join(test_path, '_external.bean')
    entries, errors, options = utils.load_ledger(source_path)

    # assumptions
    assert not errors
    assert 'include' in options
    assert external_path not in options['include']

    entries, errors = utils.apply_plugin(plugin, entries, options, None)

    assert not errors, errors
    assert external_path in options['include'], 'included files not added into options["include"]'
