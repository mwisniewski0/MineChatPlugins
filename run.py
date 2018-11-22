import asyncio
import atexit
import re
import subprocess
from typing import Dict

import monitoring
import plugins as plugins_loader
import stdin_handler
from commands import ServerCommandExecutor

from config import CONFIG
from rcon import RconConnection


async def program_loop(plugins: Dict[str, plugins_loader.Plugin],
                       log_source: monitoring.LogMonitor):
    await asyncio.wait([plugin.on_load(plugins) for plugin in plugins.values()])
    while True:
        lines = await log_source.get_new_log_lines()
        for line in lines:
            await asyncio.wait([plugin.handle_line(line) for plugin in plugins.values()])


async def program():
    if CONFIG['server_start_command'] is None and\
            (CONFIG['command_sink'] == 'subprocess' or CONFIG['log_source'] == 'subprocess'):
        print('You need to provide a server_start_command if your command_sink or log_source '
              'are set to "subprocess"')
        return

    server_process = None
    if CONFIG['server_start_command'] is not None:
        stdin_pipe_setting = \
            subprocess.PIPE if CONFIG['command_sink'] == 'subprocess' else subprocess.DEVNULL
        stdout_pipe_setting =\
            subprocess.PIPE if CONFIG['log_source'] == 'subprocess' else subprocess.DEVNULL
        server_process = subprocess.Popen(CONFIG['server_start_command'], shell=True,
                                          stdin=stdin_pipe_setting, stdout=stdout_pipe_setting)
        atexit.register(lambda: server_process.kill())

    command_sink = None
    log_source = None

    if CONFIG['command_sink'] == 'subprocess':
        command_sink = stdin_handler.StdinHandler(server_process.stdin)
    elif CONFIG['command_sink'].startswith('rcon:'):
        [_, port, password] = CONFIG['command_sink'].split(':', 2)
        command_sink = RconConnection()
        await command_sink.connect(int(port), password)
    else:
        print('Invalid "command_sink" value')
        return

    if CONFIG['log_source'] == 'subprocess':
        log_source = monitoring.StdoutMonitor(server_process.stdout)
    else:
        log_source = monitoring.FileMonitor(CONFIG['log_source'])

    plugins = plugins_loader.load_plugins(CONFIG['plugins_directory'], command_sink)
    await program_loop(plugins, log_source)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(program())


