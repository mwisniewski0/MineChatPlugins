import unittest
from datetime import datetime

from log_lines import LogLine


class TestLogLines(unittest.TestCase):
    def test_parse_main_warn(self):
        line = '[22:19:38] [main/WARN]: Ambiguity between arguments [teleport, destination] and [teleport, targets] with inputs: [Player, 0123, @e, dd12be42-52a9-4a91-a8a1-11c01849e498]'
        log_line = LogLine.parse_log_line(line, datetime(2001, 4, 13, 22, 20, 1))
        self.assertEqual(datetime(2001, 4, 13, 22, 19, 38), log_line.timestamp)
        self.assertEqual('Ambiguity between arguments [teleport, destination] and [teleport, targets] with inputs: [Player, 0123, @e, dd12be42-52a9-4a91-a8a1-11c01849e498]', log_line.content)
        self.assertEqual('main/WARN', log_line.category)


if __name__ == '__main__':
    unittest.main()
