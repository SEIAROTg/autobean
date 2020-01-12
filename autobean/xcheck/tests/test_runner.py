import os.path
from autobean.xcheck import plugin
from autobean.utils.plugin_test_utils import generate_tests


@generate_tests(os.path.dirname(__file__), plugin)
def test():
    pass
