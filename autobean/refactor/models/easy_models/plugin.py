from autobean.refactor.models.raw_models import plugin
from . import internal


class Plugin(plugin.Plugin):
    name = internal.required_string_property(plugin.Plugin.raw_name)
    config = internal.optional_string_property(plugin.Plugin.raw_config)
