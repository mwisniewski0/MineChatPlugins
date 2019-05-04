import asyncio
import os
from abc import ABC
from datetime import datetime
from typing import List
import abc

from log_lines import LogLine


class LogMonitor(abc.ABC):
    @abc.abstractmethod
    async def get_new_log_lines(self) -> List[LogLine]:
        raise NotImplementedError()


class _StdoutReader:
    def __init__(self, stdout, loop=asyncio.get_event_loop()):
        self.stdin = stdout
        self.loop = loop

    async def readline(self):
        # a single call to sys.stdin.readline() is thread-safe
        return await self.loop.run_in_executor(None, self.stdin.readline)


class StdoutMonitor(LogMonitor):
    def __init__(self, stdout_pipe, passthrough=True):
        self._passthrough = passthrough
        self._pipe = _StdoutReader(stdout_pipe)

        # Remainder from last read, if it did not include a full line
        self._last_line = b''

    async def get_new_log_lines(self) -> List[LogLine]:
        line = await self._pipe.readline()
        if line.endswith(b'\n'):
            result = (self._last_line + line[:-1]).decode()

            if self._passthrough:
                print(result)

            # Fixing messy line ends on Windows
            if result[-1] == '\r':
                result = result[:-1]

            self._last_line = b''
            return [LogLine.parse_log_line(result, datetime.utcnow())]
        else:
            self._last_line += line
            return []


class FileMonitor(LogMonitor):
    def __init__(self, log_path: str):
        self._log_path = log_path
        self._last_location = 0

    async def get_new_log_lines(self) -> List[LogLine]:
        text_lines = []
        with open(self._log_path, 'r') as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()

            if file_size < self._last_location:
                # Log must have been purged
                self._last_location = 0

            f.seek(self._last_location)
            text_lines = [l[0:-1] for l in f.readlines()]  # strip the new-line character from lines
            self._last_location = f.tell()

        log_lines = []
        for line in text_lines:
            log_lines.append(LogLine.parse_log_line(line, datetime.utcnow()))
        return log_lines

