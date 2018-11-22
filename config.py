CONFIG = {
    # Note - if either command_sink or log_source is set to subprocess
    'server_start_command': 'java -Xmx1024M -Xms1024M -jar C:\\Users\\m_wis\\Desktop\\tests\\server.jar nogui',  # Can be None if command_sink and log_source are both not
                                   # 'subprocess'
    'command_sink': 'subprocess',  # or rcon:<port_number>:<password>
    'log_source': 'subprocess',  # or <path to the latest.log file>
    'plugins_directory': './plugins',
}
