import asyncio
import atexit
import re
import shlex
import subprocess
import threading
import traceback
from typing import Dict
import sys

import monitoring
import plugins as plugins_loader
import stdin_handler
from commands import ServerCommandExecutor

from config import CONFIG
from rcon import RconConnection


SERVER_POLL_INTERVAL = 20.0


async def program_loop(plugins: Dict[str, plugins_loader.Plugin],
                       log_source: monitoring.LogMonitor):
    sorted_plugins = plugins_loader.sort_plugins_topologically(plugins)
    try:
        await asyncio.gather(*[plugin.on_load(plugins) for plugin in sorted_plugins])
    except SystemExit as e:
        raise
    except Exception as e:
        traceback.print_exc()
        return

    while True:
        try:
            lines = await log_source.get_new_log_lines()
            for line in lines:
                await asyncio.gather(*[plugin.handle_line(line) for plugin in sorted_plugins])
        except SystemExit as e:
            raise
        except Exception as e:
            traceback.print_exc()


async def program():
    if CONFIG['server_start_command'] is None and \
            (CONFIG['command_sink'] == 'subprocess' or CONFIG['log_source'] == 'subprocess'):
        print('You need to provide a server_start_command if your command_sink or log_source '
              'are set to "subprocess"')
        return

    server_process = None
    if CONFIG['server_start_command'] is not None:
        stdin_pipe_setting = \
            subprocess.PIPE if CONFIG['command_sink'] == 'subprocess' else subprocess.DEVNULL
        stdout_pipe_setting = \
            subprocess.PIPE if CONFIG['log_source'] == 'subprocess' else subprocess.DEVNULL
        server_process = subprocess.Popen(shlex.split(CONFIG['server_start_command']), shell=False,
                                          stdin=stdin_pipe_setting, stdout=stdout_pipe_setting)

        # We need to kill this process if the server dies
        async def kill_main_thread_coro():
            exit(1)

        asyncio_loop = asyncio.get_event_loop()
        def monitor_subprocess():
            while True:
                try:
                    server_process.wait(SERVER_POLL_INTERVAL)
                    asyncio.run_coroutine_threadsafe(kill_main_thread_coro(), asyncio_loop)
                    break
                except subprocess.TimeoutExpired:
                    pass

        monitor_thread = threading.Thread(target=monitor_subprocess)
        monitor_thread.setDaemon(True)
        monitor_thread.start()

        # Let Minecraft start
        await asyncio.sleep(CONFIG['minecraft_wait_timeout'])
        atexit.register(
            lambda: server_process.kill())

    command_sink = None
    log_source = None

    if CONFIG['log_source'] == 'subprocess':
        log_source = monitoring.StdoutMonitor(server_process.stdout)
    else:
        log_source = monitoring.FileMonitor(CONFIG['log_source'])

    if CONFIG['command_sink'] == 'subprocess':
        command_sink = stdin_handler.StdinHandler(server_process.stdin)
    elif CONFIG['command_sink'].startswith('rcon:'):
        [_, port, password] = CONFIG['command_sink'].split(':', 2)
        command_sink = RconConnection()
        await command_sink.connect(int(port), password)
        asyncio.ensure_future(command_sink.server_communication_loop())
    else:
        print('Invalid "command_sink" value')
        return

    plugins = plugins_loader.load_plugins(CONFIG['plugins_directory'], command_sink)
    await program_loop(plugins, log_source)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(program())


