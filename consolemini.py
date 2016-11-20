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

        with open(self.db_filepath, 'r+') as f:
            json.dump(new_data, f, indent=2)

        return self.read_db()

    def read_db(self, game_id=None):
        with open(self.db_filepath, 'r') as f:
            cm_data = json.load(f)

        # This allow us to query the ConsoleMini JSON file,
        # and in the case we didn't asked for a specific game_id:
        # We just read the whole ConsoleMini JSON file
        return cm_data[game_id] if game_id else cm_data

    def parse_chat_message(self, chat_message):
        """
        Parse bits/chat message to detect which game_id was cheered
        >>> chat_message = "Omg that baneling bust was Kreygasm CM16 cheer10 cheer10 cheer100"
        >>> cm_index = chat_message.lower().find('cm')
        36
        In this case game_id will be 'CM16'.

        >>> chat_message = "cheer500 Sed ut error sit voluptatem cm 10"
        >>> cm_index = chat_message.lower().find('cm')
        37
        >>> message_data = chat_message[cm_index:].split()
        ['cm', '10']
        In this case game_id will be 'CM10'.
        """
        cm_index = chat_message.lower().find('cm')
        # rule_index = chat_message.lower().find('re')

        if cm_index:
            # Detecting which game_id was cheered
            message_data = chat_message[cm_index:].split()
            try:
                game_id = message_data[0]
                if len(message_data[0]) == 2 and int(message_data[1]):
                    game_id = '{}{}'.format(message_data[0], message_data[1])
            except (IndexError, ValueError):
                return None

            # Remember: game_ids in JSON are in UPPERCASE.
            return game_id.upper()
        # elif rule_index:
        else:
            return None

    def write_trending_files(self, trending_games):
        """
        Finally update ConsoleMini trending games (3) text files
        """
        for index, game in enumerate(trending_games):
            with open(os.path.join(self.db_dirname, 'consolemini.{}.txt'.format(index + 1)), 'w') as f:
                f.write('{} : {} bits'.format(game['game_name'], game['total_bits']))

    def update_trending_games(self, chat_message, bits_used):
        # Parse bits/chat message to detect which game_id was cheered
        game_id = self.parse_chat_message(chat_message)
        if not game_id:
            return False

        # Update ConsoleMini JSON file accordingly
        cm_data = self.read_db()
        if not cm_data:
            return False

        game_data = cm_data[game_id]
        game_data['total_bits'] += int(bits_used)
        self.log.info('{} has now {} bits !'.format(game_data['game_name'], game_data['total_bits']))
        updated_data = self.write_db(game_id, game_data)

        # updated_data is the now updated ConsoleMini JSON file.
        # We need to parse it and build a list following this model:
        # [{'total_bits': 700, 'game_name': 'Kid Chameleon'},
        #  {'total_bits': 300, 'game_name': 'Rocket Knight Adventures'},
        #  {'total_bits': 100, 'game_name': 'Ecco'}]

        trending_games = sorted([updated_data[game]
                                for game in updated_data
                                if updated_data[game]['total_bits'] != 0],
                                key=lambda k: k['total_bits'],
                                reverse=True)[:3]
        self.log.info('Here is the new 3 trending games :')
        self.log.info(trending_games)

        # Finally update ConsoleMini trending games text files
        self.write_trending_files(trending_games)
