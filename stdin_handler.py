import asyncio
import os
import sys
import threading

from commands import ServerCommandExecutor


class StdinHandler(ServerCommandExecutor):
    def __init__(self, stdin_pipe, passthrough=True):
        self.stdin_pipe = stdin_pipe

        if passthrough:
            def stdin_thread():
                while True:
                    line = sys.stdin.readline()
                    self.stdin_pipe.write(line.encode())
            thread = threading.Thread(target=stdin_thread)
            thread.start()

    def _passthrough_loop(self):
        lines = sys.stdin.readlines()

    async def send_command(self, command: str) -> str:
        self.stdin_pipe.write(b'/' + command.encode() + os.linesep.encode())
        self.stdin_pipe.flush()
        return ''  # not available using the StdinHandler
