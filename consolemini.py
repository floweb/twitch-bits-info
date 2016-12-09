import json
import os

import requests


class BadArgsException(Exception):
    def __init__(self, missing_params):
        message = ("You must set at least one of these arg "
                   "for this function: {}".format(', '.join(missing_params)))
        print(message)
        super(BadArgsException, self).__init__(message)


class ConsoleMini(object):

    def __init__(self, **kwargs):
        # Setup this class attributes, logs, etc...
        self.__dict__.update(kwargs)
        self.db_dirname = os.path.dirname(self.db_filepath)

    def write_db(self, game_id=None, current_game=None, new_data=None):
        if not game_id and not current_game and not new_data:
            raise BadArgsException(['game_id', 'current_game', 'new_data'])

        if new_data:
            try:
                for game_id in new_data:
                    requests.post('{}/{}'.format(self.api_url, game_id),
                                  json=new_data[game_id], headers={'X-CM-API-KEY': self.api_key})
            except AttributeError:
                pass

        if game_id and current_game and not new_data:
            new_data = self.read_db()

            item_to_remove = [item
                              for item in new_data['games']
                              if item['id'] == game_id][0]
            new_data['games'].remove(item_to_remove)
            new_data['games'].append(current_game)

            try:
                requests.post('{}/{}'.format(self.api_url, game_id),
                              json=current_game, headers={'X-CM-API-KEY': self.api_key})
            except AttributeError:
                pass

        with open(self.db_filepath, 'w') as f:
            json.dump(new_data, f, indent=2, sort_keys=True)

        return self.read_db()

    def read_db(self, game_id=None):
        with open(self.db_filepath, 'r') as f:
            cm_data = json.load(f)

        # This allow us to query the ConsoleMini JSON file
        if game_id:
            try:
                game_data = [game
                             for game in cm_data['games']
                             if game['id'] == game_id][0]
            except (IndexError, KeyError):
                return None

            return game_data

        # And in the case we didn't asked for a specific game_id,
        # we just read the whole ConsoleMini JSON file
        return cm_data

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

        if cm_index == -1:
            return None

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

    def write_trending_files(self, trending_games):
        """
        Finally update ConsoleMini trending games (3) text files:
        Example trending_games:
        [{'total_bits': 300, 'game_name': 'Kid Chameleon', 'priority': 9},
         {'total_bits': 300, 'game_name': 'Rocket Knight Adventures', 'priority': 10},
         {'total_bits': 100, 'game_name': 'Ecco', 'priority': 10}]
        """
        for index, game in enumerate(trending_games):
            with open(os.path.join(self.db_dirname, 'consolemini.{}.txt'.format(index + 1)), 'w') as f:
                f.write('{} : {} bits'.format(game['game_name'], game['total_bits']))

    def reset_priority(self, cm_data, total_bits, current_game_id=None):
        """
        To set our current game its new priority,
        we need to detect every game (including our current game)
        which already has the same amount of bits,
        and reset their priority to the default (which is 10).
        """
        games_reseted = False
        for index, _ in enumerate(cm_data['games']):
            if (cm_data['games'][index]['total_bits'] == total_bits and
               cm_data['games'][index]['id'] != current_game_id):
                games_reseted = True
                cm_data['games'][index]['priority'] = 10

        return self.write_db(new_data=cm_data) if games_reseted else cm_data

    def update_trending_games(self, chat_message=None, bits_used=None):
        """
        Main function for ConsoleMini.
        """
        if chat_message and bits_used:
            # Parse bits/chat message to detect which game_id was cheered
            game_id = self.parse_chat_message(chat_message)
            if game_id is None:
                return False

            # Update ConsoleMini JSON file accordingly
            cm_data = self.read_db()
            current_game = [game
                            for game in cm_data['games']
                            if game['id'] == game_id][0]
            current_game['total_bits'] += int(bits_used)
            current_game['priority'] -= 1

            # To set our current game its new priority,
            # we need to detect every game (including our current game)
            # which already has the same amount of bits,
            # and reset their priority to the default (which is 10).
            cm_data = self.reset_priority(cm_data, current_game['total_bits'], game_id)

            item_to_remove = [item
                              for item in cm_data['games']
                              if item['id'] == game_id][0]
            cm_data['games'].remove(item_to_remove)
            cm_data['games'].append(current_game)

            self.log.info('{} has now {} bits, and its priority is {} !'.format(
                current_game['game_name'], current_game['total_bits'], current_game['priority']))
            updated_data = self.write_db(new_data=cm_data)

        elif chat_message is None and bits_used is None:
            updated_data = self.read_db()
        else:
            return False

        # updated_data is the now updated ConsoleMini JSON file.
        # We need to parse it and build a list following this model:
        # Firstly we sort by total_bits DESC, and then by priority ASC.
        # [{'total_bits': 300, 'game_name': 'Kid Chameleon', 'priority': 9},
        #  {'total_bits': 300, 'game_name': 'Rocket Knight Adventures', 'priority': 10},
        #  {'total_bits': 100, 'game_name': 'Ecco', 'priority': 10}]

        trending_games = sorted([game
                                 for game in updated_data['games']],
                                key=lambda k: (-k['total_bits'], k['priority']))[:3]

        self.log.info('Here is the new 3 trending games : {}'.format(trending_games))

        # Finally update ConsoleMini trending games text files
        self.write_trending_files(trending_games)

        return True
