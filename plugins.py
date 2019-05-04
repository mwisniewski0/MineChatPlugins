import abc
import importlib
import pkgutil
import sys
from typing import Dict, List

from commands import ServerCommandExecutor
from log_lines import LogLine


class Plugin(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def create(cls, command_sink: ServerCommandExecutor) -> 'Plugin':
        raise NotImplementedError()

    @abc.abstractmethod
    def get_dependencies(self) -> [str]:
        """
        Returns the list of names of plugins that this plugin is dependent on. This is used to
        perform a topological sort on the plugins. You are guaranteed that the plugins you mentioned
        were updated before this plugin in a given update chain (on load, for a given chat line,
        etc.)
        """
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
    # TODO: unnecessary?
    global loaded_plugins
    sys.path.insert(0, plugins_path)

    pkgutil.iter_modules(plugins_path)
    for importer, modname, ispkg in pkgutil.iter_modules([plugins_path]):
        if ispkg:
            continue
        importlib.import_module(modname)

    return {
        name: plugin_class.create(command_sink) for name, plugin_class in plugin_classes.items()
    }


def sort_plugins_topologically(plugins: Dict[str, Plugin]) -> List[Plugin]:
    # Make a copy of plugins so that the original input is not affected
    plugins = {k: v for (k, v) in plugins.items()}

    sorted_plugins = []

    # Used to detect cycles
    visited = set()

    # Set of names in sorted_plugins
    added = set()

    def process(name, plugin):
        if name in visited:
            raise ValueError('Cycle containing "' + name + '" in the plugin list')
        visited.add(name)

        for dependency_name in plugin.get_dependencies():
            if dependency_name in added:
                continue
            if dependency_name not in plugins:
                raise ValueError('Plugin "' + name + '" required "' + dependency_name +
                                 '" which was not included')
            dependency_plugin = plugins[dependency_name]
            del plugins[dependency_name]
            process(dependency_name, dependency_plugin)

        sorted_plugins.append(plugin)
        added.add(name)

    while len(plugins) != 0:
        (name, plugin) = plugins.popitem()
        process(name, plugin)

    return sorted_plugins
