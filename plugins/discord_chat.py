import asyncio

import discord

from typing import Dict

from commands import ServerCommandExecutor
from log_lines import LogLine, PlayerJoinedLine, PlayerMessageLine, PlayerLeftLine
from plugins import Plugin, register_plugin
from discord_chat_config import DISCORD_CONFIG
from utils import fire_and_forget


@register_plugin
class DiscordChat(Plugin):
    def __init__(self, command_sink: ServerCommandExecutor):
        self.command_sink = command_sink
        self.client = discord.Client()
        self.plugins = {}
        self.channel_id = DISCORD_CONFIG['channel_id']
        self.channel = None

        @self.client.event
        async def on_ready():
            self.channel = self.client.get_channel(self.channel_id)

        @self.client.event
        async def on_message(message):
            if message.channel.id != self.channel_id:
                return

            if message.author == self.client.user:
                return
            if message.content == '!list':
                players = self.plugins['PlayerListPlugin'].players
                message = str(len(players)) + ' players on the server: ' + ', '.join(players)
                await self.channel.send(message)
            else:
                await self.command_sink.server_say(
                    '(Discord: ' + message.author.name + ') ' + message.content)

    def get_dependencies(self) -> [str]:
        return ['PlayerListPlugin']

    @classmethod
    def create(cls, command_sink: ServerCommandExecutor) -> Plugin:
        return DiscordChat(command_sink)

    async def on_load(self, all_plugins: Dict[str, Plugin]):
        self.plugins = all_plugins

        # This will add the client to the asyncio loop
        fire_and_forget(
            self.client.start(DISCORD_CONFIG['token'])
        )
        a = 4

    async def handle_line(self, line: LogLine):
        if isinstance(line, PlayerJoinedLine):
            await self.channel.send(line.content)
        elif isinstance(line, PlayerLeftLine):
            await self.channel.send(line.content)
        elif isinstance(line, PlayerMessageLine):
            await self.channel.send(line.player_name + ': ' + line.message_text)
