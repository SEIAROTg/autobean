import os.path
import pytest
from autobean.narration import plugin
from autobean.utils.plugin_test_util import PluginTestUtil


@pytest.fixture('module')
def util() -> PluginTestUtil:
    return PluginTestUtil(os.path.dirname(__file__), plugin)


def test_simple(util: PluginTestUtil):
    util.assert_results('simple', [None])


def test_comments(util: PluginTestUtil):
    util.assert_results('comments', [None])
