import difflib
from typing import Dict

from commands import ServerCommandExecutor
from log_lines import LogLine, PlayerJoinedLine, PlayerMessageLine, PlayerLeftLine
from plugins import Plugin, register_plugin


@register_plugin
class PlayerListPlugin(Plugin):
    def __init__(self, command_sink: ServerCommandExecutor):
        self.command_sink = command_sink
        self.players = set()

    def get_dependencies(self) -> [str]:
        return []

    @classmethod
    def create(cls, command_sink: ServerCommandExecutor) -> Plugin:
        return PlayerListPlugin(command_sink)

    async def on_load(self, all_plugins: Dict[str, Plugin]):
        pass

    async def handle_line(self, line: LogLine):
        if line.content.startswith('Starting minecraft server'):
            print('resetting player list')
            self.players = set()
        elif isinstance(line, PlayerJoinedLine):
            self.players.add(line.player_name)
        elif isinstance(line, PlayerLeftLine):
            self.players.remove(line.player_name)
