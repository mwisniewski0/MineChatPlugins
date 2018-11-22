import abc
import importlib
import pkgutil
import sys
from typing import Dict

from commands import ServerCommandExecutor
from log_lines import LogLine


class Plugin(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def create(cls, command_sink: ServerCommandExecutor) -> 'Plugin':
        raise NotImplementedError()

    @abc.abstractmethod
    async def on_load(self, all_plugins: Dict[str, 'Plugin']):
        raise NotImplementedError()

    @abc.abstractmethod
    async def handle_line(self, line: LogLine):
        raise NotImplementedError()


plugin_classes = {}


def register_plugin(plugin_class, name=None):
    if name is None:
        name = plugin_class.__name__
    if name in plugin_classes:
        raise ValueError('Plugin ' + name + ' already exists')
    else:
        plugin_classes[name] = plugin_class

    return plugin_class


def load_plugins(plugins_path: str, command_sink: ServerCommandExecutor) -> Dict[str, Plugin]:
    global loaded_plugins
    sys.path.insert(0, plugins_path)

    pkgutil.iter_modules(plugins_path)
    for importer, modname, ispkg in pkgutil.iter_modules([plugins_path]):
        print(importer, modname, ispkg)
        if ispkg:
            continue
        importlib.import_module(modname)

    return {
        name: plugin_class.create(command_sink) for name, plugin_class in plugin_classes.items()
    }
