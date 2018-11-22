import abc


class ServerCommandExecutor(abc.ABC):
    @abc.abstractmethod
    async def send_command(self, command: str) -> str:
        raise NotImplementedError()

    async def server_say(self, message: str):
        await self.send_command('say ' + message)
