import unittest
from datetime import datetime
from typing import Dict

from commands import ServerCommandExecutor
from log_lines import LogLine
from plugins import Plugin, sort_plugins_topologically


class P(Plugin):
    def __init__(self, name, deps):
        self.deps = deps
        self.name = name

    @classmethod
    def create(cls, command_sink: ServerCommandExecutor) -> 'Plugin':
        pass

    def get_dependencies(self) -> [str]:
        return self.deps

    async def on_load(self, all_plugins: Dict[str, 'Plugin']):
        pass

    async def handle_line(self, line: LogLine):
        pass


class TestPlugins(unittest.TestCase):
    def test_topo_sort_1(self):
        p1 = P('p1', ['p2','p3'])
        p2 = P('p2', ['p4'])
        p3 = P('p3', ['p4'])
        p4 = P('p4', [])
        p5 = P('p5', ['p6'])
        p6 = P('p6', [])

        plugins = {
            'p1': p1,
            'p2': p2,
            'p3': p3,
            'p4': p4,
            'p5': p5,
            'p6': p6,
        }

        sorted_plugins = sort_plugins_topologically(plugins)
        sorted_names = [plugin.name for plugin in sorted_plugins]

        self.assertIn(sorted_names, [
            ['p4', 'p3', 'p2', 'p1', 'p6', 'p5'],
            ['p4', 'p2', 'p3', 'p1', 'p6', 'p5'],
            ['p6', 'p5', 'p4', 'p3', 'p2', 'p1'],
            ['p6', 'p5', 'p4', 'p2', 'p3', 'p1'],
        ])

    def test_topo_sort_2(self):
        p1 = P('p1', ['p4', 'p3'])
        p2 = P('p2', ['p1'])
        p3 = P('p3', ['p4'])
        p4 = P('p4', [])
        p5 = P('p5', [])
        p6 = P('p6', ['p5'])

        plugins = {
            'p1': p1,
            'p2': p2,
            'p3': p3,
            'p4': p4,
            'p5': p5,
            'p6': p6,
        }

        sorted_plugins = sort_plugins_topologically(plugins)
        sorted_names = [plugin.name for plugin in sorted_plugins]

        self.assertIn(sorted_names, [
            ['p4', 'p3', 'p1', 'p2', 'p5', 'p6'],
            ['p5', 'p6', 'p4', 'p3', 'p1', 'p2'],
        ])

    def test_topo_sort_finds_missing_deps(self):
        p1 = P('p1', ['p4', 'p3'])
        p2 = P('p2', ['p1'])
        p3 = P('p3', ['p4'])
        p4 = P('p4', ['p7'])
        p5 = P('p5', [])
        p6 = P('p6', ['p5'])

        plugins = {
            'p1': p1,
            'p2': p2,
            'p3': p3,
            'p4': p4,
            'p5': p5,
            'p6': p6,
        }
        self.assertRaises(ValueError, lambda: sort_plugins_topologically(plugins))

    def test_topo_sort_finds_cycles(self):
        p1 = P('p1', ['p4', 'p3'])
        p2 = P('p2', ['p1'])
        p3 = P('p3', ['p4'])
        p4 = P('p4', ['p1'])
        p5 = P('p5', [])
        p6 = P('p6', ['p5'])

        plugins = {
            'p1': p1,
            'p2': p2,
            'p3': p3,
            'p4': p4,
            'p5': p5,
            'p6': p6,
        }
        self.assertRaises(ValueError, lambda: sort_plugins_topologically(plugins))


if __name__ == '__main__':
    unittest.main()
