from typing import Dict

from commands import ServerCommandExecutor
from log_lines import LogLine, PlayerJoinedLine, PlayerMessageLine
from plugins import Plugin


DEBUG = True


class PlayerListPlugin(Plugin):
    def __init__(self, command_sink: ServerCommandExecutor):
        self.command_sink = command_sink
        self.players = set()

    @classmethod
    def create(cls, command_sink: ServerCommandExecutor) -> Plugin:
        return PlayerListPlugin(command_sink)

    async def on_load(self, all_plugins: Dict[str, Plugin]):
        pass

    async def handle_line(self, line: LogLine):
        if line.content.startswith('Starting minecraft server'):
            self.players = set()
        elif isinstance(line, PlayerJoinedLine):
            self.players.add(line.player_name)
        elif isinstance(line, PlayerJoinedLine):
            self.players.remove(line.player_name)
        elif isinstance(line, PlayerMessageLine):
            if DEBUG:
                if line.message_text == '$list_players':
                    await self.command_sink.server_say(','.join(self.players))
