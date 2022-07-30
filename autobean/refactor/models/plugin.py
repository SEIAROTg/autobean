from typing import Optional, Type, TypeVar
from . import internal
from .escaped_string import EscapedString
from .generated import plugin
from .generated.plugin import PluginLabel

_Self = TypeVar('_Self', bound='Plugin')


@internal.tree_model
class Plugin(plugin.Plugin):
    name = internal.required_string_property(plugin.Plugin.raw_name)
    config = internal.optional_string_property(plugin.Plugin.raw_config, EscapedString)

    @classmethod
    def from_value(cls: Type[_Self], name: str, config: Optional[str] = None) -> _Self:
        return cls.from_children(
            EscapedString.from_value(name),
            EscapedString.from_value(config) if config is not None else None)
