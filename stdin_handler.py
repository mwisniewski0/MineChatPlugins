from commands import ServerCommandExecutor


class StdinHandler(ServerCommandExecutor):
    def __init__(self, stdin_pipe):
        self.stdin_pipe = stdin_pipe

    async def send_command(self, command: str) -> str:
        self.stdin_pipe.write(b'/' + command.encode())
        return ''  # not available using the StdinHandler
