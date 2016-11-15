from collections import OrderedDict
import json
import os


class ConsoleMini(object):

    def __init__(self, **kwargs):
        # Setup this class attributes, logs, etc...
        self.__dict__.update(kwargs)
        self.db_dirname = os.path.dirname(self.db_filepath)

    def write_db(self, game_id, game_data):
        new_data = self.read_db()
        new_data[game_id] = game_data

        with open(self.db_path, 'r+') as f:
            res = json.dump(new_data, f)
        return res

    def read_db(self, game_id=None):
        with open(self.db_path, 'r') as f:
            cm_data = json.load(f)

        if game_id and game_id == cm_data['game_id']:
            # This allow us to query the ConsoleMini JSON file
            return cm_data['game_id']
        elif not game_id:
            # In the case we didn't asked for a query, we just read the ConsoleMini JSON file
            return cm_data

    def parse_chat_message(self, chat_message):
        """
        Parse bits/chat message to detect which game_id was cheered
        """
        game_id = chat_message
        return game_id

    def write_trending_files(self, trending_games):
        """
        Finally update ConsoleMini trending games (3) text files
        """
        for index, game in enumerate(trending_games):
            with open(os.path.join(self.db_dirname, 'consolemini.{}.txt'.format(index + 1)), 'w') as f:
                f.write(trending_games[index])

    def update_trending_games(self, chat_message, bits_used):
        # Parse bits/chat message to detect which game_id was cheered
        game_id = self.parse_chat_message(chat_message)

        # Update ConsoleMini JSON file accordingly
        game_data = self.read_db(game_id)
        cm_data = self.write_db(game_id, game_data)

        # cm_data is the updated & sorted ConsoleMini JSON file.
        # We need to parse it and build a list following this model:
        # ['Soleil: 300 bits', 'Ecco: 200 bits', 'Kid Chameleon: 100 bits']
        cm_data
        trending_games = []

        # Finally update ConsoleMini trending games text files
        self.write_trending_files(trending_games)
