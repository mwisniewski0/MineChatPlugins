import datetime
import re


class LogLine:
    def __init__(self, timestamp: datetime.datetime, category: str, content: str):
        self.content = content
        self.category = category
        self.timestamp = timestamp

    @staticmethod
    def _deduce_timestamp(time: datetime.datetime, read_on: datetime.datetime):
        current_day = time.replace(year=read_on.year, month=read_on.month, day=read_on.day)
        day_before = current_day - datetime.timedelta(days=1)
        day_after = current_day + datetime.timedelta(days=1)

        candidates = [current_day, day_before, day_after]

        best_candidate = None
        best_candidate_diff = datetime.timedelta.max
        for candidate in candidates:
            diff = abs(read_on - candidate)
            if best_candidate_diff >= diff:
                best_candidate = candidate
                best_candidate_diff = diff
        return best_candidate

    @staticmethod
    def parse_log_line(line: str, read_on: datetime.datetime):
        print(line)
        # Logs are in the form [HH:MM:SS] [<category>]: <content>. Time is in military format.
        time_string = ''
        category_string = ''
        content_string = ''

        state = 'start_time'
        for c in line:
            if state == 'start_time':
                if c != '[':
                    raise ValueError('A log line must start with "["')
                state = 'time'
            elif state == 'time':
                if c == ']':
                    state = 'start_category'
                else:
                    time_string += c
            elif state == 'start_category':
                if c == '[':
                    state = 'category'
            elif state == 'category':
                if c == ']':
                    state = 'start_content'
                else:
                    category_string += c
            elif state == 'start_content':
                if c == ' ':
                    state = 'content'
            elif state == 'content':
                content_string += c
            else:
                raise RuntimeError('Invalid state: ' + state)

        if state != 'content':
            raise ValueError('The line ' + line + ' does not have the required, 3-part format')

        timestamp = LogLine._deduce_timestamp(datetime.datetime.strptime(time_string, '%H:%M:%S'),
                                              read_on)

        return LogLine(timestamp, category_string, content_string)._specialized()

    def _specialized(self):
        if self.category == 'Server thread/INFO':
            if re.fullmatch('<.*> .*', self.content):
                name_end_index = self.content.find('>')
                player_name = self.content[1:name_end_index]
                player_message = self.content[name_end_index + 2:]
                return PlayerMessageLine(self, player_name, player_message)
            elif re.fullmatch('\[Server\] .*', self.content):
                message = self.content[self.content.find(']') + 2:]
                return ServerMessage(self, message)
            elif self.content.endswith(' joined the game'):
                return PlayerJoinedLine(self, self.content[:-len(' joined the game')])
            elif self.content.endswith(' left the game'):
                return PlayerLeftLine(self, self.content[:-len(' left the game')])
        return self

    
class ServerMessage(LogLine):
    def __init__(self, base: LogLine, message_text: str):
        LogLine.__init__(self, base.timestamp, base.category, base.content)
        self.message_text = message_text


class PlayerMessageLine(LogLine):
    def __init__(self, base: LogLine, player_name: str, message_text: str):
        LogLine.__init__(self, base.timestamp, base.category, base.content)
        self.message_text = message_text
        self.player_name = player_name


class PlayerJoinedLine(LogLine):
    def __init__(self, base: LogLine, player_name: str):
        LogLine.__init__(self, base.timestamp, base.category, base.content)
        self.player_name = player_name


class PlayerLeftLine(LogLine):
    def __init__(self, base: LogLine, player_name: str):
        LogLine.__init__(self, base.timestamp, base.category, base.content)
        self.player_name = player_name
