import os.path
import sys
from autobean.share import plugin
from autobean.utils import plugin_test_utils


@plugin_test_utils.generate_tests(os.path.dirname(__file__), plugin.Plugin.plugin)
def test() -> None:
    pass


if __name__ == '__main__':
    plugin_test_utils.generate_goldens(
        os.path.dirname(__file__), sys.argv[1], plugin.Plugin.plugin)
