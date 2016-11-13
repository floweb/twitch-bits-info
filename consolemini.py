import io
import sys

if sys.version_info[0] >= 3:
    import csv  # Hello, dear Python 3+ user
else:
    from backports import csv


class ConsoleMini(object):

    def __init__(self, **kwargs):
        # Setup this class attributes, logs, etc...
        self.__dict__.update(kwargs)

    def write_to_db(self, data):
        with io.open(self.db_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f)
            for row in data:
                writer.writerows(row)

    def read_db(self, game_id=None, game_name=None, total_bits=None):
        with io.open(self.db_path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                # This allow us to query the ConsoleMini CSV file
                if game_id and game_id == row['game_id']:
                    yield row
                    break
                if game_name and game_name == row['game_name']:
                    yield row
                    break
                if total_bits and total_bits == row['total_bits']:
                    yield row
                    break

                # In the case we didn't asked for a query, we just read the ConsoleMini CSV file
                if not game_id and not game_name and not total_bits:
                    yield row

    def parse_chat_message(self, chat_message):
        """
        We need to parse the chat_message to detect which game_id or game_name was cheered.
        """
        chat_message

    def write_trending_files(self, chat_message):
        """
        We need to parse the chat_message to detect which game_id or game_name was cheered.
        """
        chat_message

    def update_trending_games(self, chat_message, bits_used):
        game_id = self.parse_chat_message(chat_message)
        data = self.read_db(game_id=game_id)
        self.write_to_db(data)
        self.write_trending_files()
