from typing import Optional, Type, TypeVar
from autobean.refactor.models.raw_models import plugin
from autobean.refactor.models.raw_models.plugin import PluginLabel
from . import internal
from .escaped_string import EscapedString

internal.token_model(PluginLabel)

_Self = TypeVar('_Self', bound='Plugin')


@internal.tree_model
class Plugin(plugin.Plugin):
    name = internal.required_string_property(plugin.Plugin.raw_name)
    config = internal.optional_escaped_string_property(plugin.Plugin.raw_config)

    @classmethod
    def from_value(cls: Type[_Self], name: str, config: Optional[str] = None) -> _Self:
        return cls.from_children(
            EscapedString.from_value(name),
            EscapedString.from_value(config) if config is not None else None)
