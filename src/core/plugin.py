from abc import ABC, abstractmethod

from core import Config, Assets
from utils import pascal2snake, log


class Plugin(ABC):
    """
    The abstract class for a bundle of Bot functionality.

    Is designed to call Bot methods on init for adding extra handlers.

    The config is the object from the item with the plugin name
    of the "plugins" object of the main config.

    To add a custom plugin:

    - Create a custom class that inherits the Plugin class.
    - Decorate the class via `@Plugin.register_plugin` decorator
      (or `@plugin` - alias from the src/core module).
    - Add a property with the plugin name to the "plugins" object
      of the main config. The value of the property must be an object as well,
      and will be passed to the plugin's constructor as <config>
      during the Bot boot.
    """

    plugins = {}

    @abstractmethod
    def __init__(self, bot, config: Config, assets: Assets):
        pass

    def finalize(self):
        """
        This method is called when the bot is stopped.
        E.g. may be used to save the state of the plugin.

        Does nothing by default.
        """
        pass

    @staticmethod
    def register_plugin(name_or_plugin: str | type):
        """
        Register a new plugin class to be available for the Bot during boot.

        The name of the plugin would be derived from the decorated class name,
        by converting the latter to snake_case. To provide a custom name,
        use `@Plugin.register_plugin("custom_plugin_name")` decorator instead
        (or `@plugin("custom_plugin_name") respectively)`

        :param name_or_plugin: custom name or the class itself
        :return: the decorated class
        """
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
