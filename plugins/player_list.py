import difflib
from typing import Dict

from commands import ServerCommandExecutor
from log_lines import LogLine, PlayerJoinedLine, PlayerMessageLine
from plugins import Plugin, register_plugin

DEBUG = True


@register_plugin
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
        print(repr(line))
        if line.content.startswith('Starting minecraft server'):
            self.players = set()
        elif isinstance(line, PlayerJoinedLine):
            self.players.add(line.player_name)
        elif isinstance(line, PlayerJoinedLine):
            self.players.remove(line.player_name)
        elif isinstance(line, PlayerMessageLine):
            print(line.player_name, line.message_text)
            if DEBUG:
                print(self.players)
                print(type(line.message_text), type('abc'))
                print(len(line.message_text), len('abc'))

                if line.message_text == 'abc':
                    print('lalallalala2')
                    await self.command_sink.server_say('[' + ','.join(self.players) + ']')

