from abc import ABC, abstractmethod

from core import Config, Assets
from utils import pascal2snake, log


class Plugin(ABC):
    plugins = {}

    @abstractmethod
    def __init__(self, bot, config: Config, assets: Assets):
        pass

    def finalize(self):
        pass

    @staticmethod
    def register_plugin(name_or_plugin: str | type):
        if not isinstance(name_or_plugin, str):
            name = pascal2snake(name_or_plugin.__name__)
            cls = name_or_plugin
            Plugin.plugins[name] = cls
            log("Plugin", "register", name)
            return cls

        name = name_or_plugin

        def decorator(cls):
            if name in Plugin.plugins:
                raise ValueError(
                    f"A plugin with name '{name}' is already registered")
            Plugin.plugins[name] = cls
            log("Plugin", "add", name)
            return cls

        return decorator
