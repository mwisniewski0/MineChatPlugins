CONFIG = {
    # Note - if either command_sink or log_source is set to subprocess
    'server_start_command': 'java -Xmx1024M -Xms1024M -jar server.jar nogui',  # Can be None if command_sink and log_source are both not
                                   # 'subprocess'
    'command_sink': 'subprocess',  # subprocess or rcon:<port_number>:<password>
    'log_source': 'subprocess',  # subprocess or <path to the latest.log file>
    'plugins_directory': './MineChatPlugins/plugins',
    'minecraft_wait_timeout': 20,  # Number of seconds the program will wait after launching minecraft before trying to connect
}
