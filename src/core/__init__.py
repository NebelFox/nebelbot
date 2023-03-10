from .config import Config
from .assets import Assets, FileAssets, yaml_assets, txt_assets
from .chat import Chat
from .help import Help
from .plugin import Plugin

plugin = Plugin.register_plugin
plugins = Plugin.plugins

from .bot import Bot
