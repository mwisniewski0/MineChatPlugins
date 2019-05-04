import asyncio
import difflib
from datetime import timedelta, datetime
from typing import Dict

import pytz

from commands import ServerCommandExecutor
from log_lines import LogLine, PlayerJoinedLine, PlayerMessageLine, PlayerLeftLine
from plugins import Plugin, register_plugin


VOTE_LIFE = timedelta(minutes=5)


@register_plugin
class VoteRestartPlugin(Plugin):
    def get_dependencies(self) -> [str]:
        return []

    def __init__(self, command_sink: ServerCommandExecutor):
        self.command_sink = command_sink
        self.players = set()
        self.votes = {}

    @classmethod
    def create(cls, command_sink: ServerCommandExecutor) -> Plugin:
        return VoteRestartPlugin(command_sink)

    async def on_load(self, all_plugins: Dict[str, Plugin]):
        pass

    async def try_after_vote_expired(self):
        await asyncio.sleep(VOTE_LIFE.total_seconds())
        await self.restart_if_votes_allow()

    async def handle_line(self, line: LogLine):
        if isinstance(line, PlayerMessageLine):
            if line.message_text == '$vote_restart':
                self.votes[line.player_name] = (True, line.timestamp)
                await self.restart_if_votes_allow()
                asyncio.ensure_future(self.try_after_vote_expired())
                await self.print_status()
            elif line.message_text == '$vote_no_restart':
                await self.restart_if_votes_allow()
                self.votes[line.player_name] = (False, line.timestamp)
                asyncio.ensure_future(self.try_after_vote_expired())
                await self.print_status()
            elif line.message_text == '$status_vote_restart':
                await self.print_status()
        elif line.content.startswith('Starting minecraft server'):
            self.players = set()
        elif isinstance(line, PlayerJoinedLine):
            self.players.add(line.player_name)
            await self.restart_if_votes_allow()
        elif isinstance(line, PlayerLeftLine):
            self.players.remove(line.player_name)
            await self.restart_if_votes_allow()

    async def print_status(self):
        yes, no = self.count_yes_no_votes()
        await self.command_sink.server_say(
            'Currently ' + str(yes) + ' votes for "yes" and ' +
            str(no) + ' votes for "no".')

    def count_yes_no_votes(self):
        now = datetime.now(pytz.utc)

        valid_yes_votes = 0
        valid_no_votes = 0
        for player, (vote, timestamp) in self.votes.items():
            if now - timestamp < VOTE_LIFE and player in self.players:
                if vote:
                    valid_yes_votes += 1
                else:
                    valid_no_votes += 1
        return valid_yes_votes, valid_no_votes

    async def restart(self):
        self.votes = {}
        await self.command_sink.server_say('Restarting...')

    async def restart_if_votes_allow(self):
        yes, no = self.count_yes_no_votes()
        player_count = len(self.players)
        if player_count == 0:
            return

        if no == 0:
            if yes / player_count > 0.3:
                await self.restart()
        else:
            if yes / player_count > 0.7:
                await self.restart()
