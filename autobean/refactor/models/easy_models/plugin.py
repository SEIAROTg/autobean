from autobean.refactor.models.raw_models import plugin
from autobean.refactor.models.raw_models.plugin import PluginLabel
from . import internal

internal.token_model(PluginLabel)


@internal.tree_model
class Plugin(plugin.Plugin):
    name = internal.required_string_property(plugin.Plugin.raw_name)
    config = internal.optional_escaped_string_property(plugin.Plugin.raw_config)
