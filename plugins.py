import abc
import importlib
import pkgutil
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


def load_plugins(plugins_path: str, command_sink: ServerCommandExecutor) -> Dict[str, Plugin]:
    loaded_plugins = {}

    pkgutil.iter_modules(plugins_path)
    for importer, modname, ispkg in pkgutil.iter_modules(plugins_path):
        if ispkg:
            continue
        module = importlib.import_module(modname)
        for name, item in module.__dict__.items():
            if isinstance(item, type) and issubclass(item, Plugin):
                plugin = item
                loaded_plugins[name] = plugin.create(command_sink)

    return loaded_plugins
