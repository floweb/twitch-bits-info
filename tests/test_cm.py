try:
    basestring
except NameError:
    basestring = str

import os
import logging

import pytest

from consolemini import ConsoleMini


@pytest.fixture(scope="module")
def cm():
    # dummy logger instance
    log = logging.getLogger('null').addHandler(logging.NullHandler())
    db_filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'consolemini.test.json')

    return ConsoleMini(db_filepath=db_filepath, log=log)


class TestConsoleMini:

    """
    write_db
    read_db
    parse_chat_message
    write_trending_files
    reset_priority
    update_trending_games
    """

    def test_write_db_nope(self, cm):
        nope = cm.write_db()
        assert nope is False

    def test_write_db_ok(self, cm):
        game_id = 'CM5'  # Fatal Rewind
        current_game = {"total_bits": 1200, "game_name": "Fatal Rewind", "priority": 8}
        res = cm.write_db(game_id=game_id, current_game=current_game)

        assert isinstance(res, dict)
        assert isinstance(res[game_id], dict)
        assert isinstance(res[game_id]['total_bits'], int)
        assert res[game_id]['total_bits'] == 1200
        assert isinstance(res[game_id]['game_name'], basestring)
        assert res[game_id]['game_name'] == 'Fatal Rewind'
        assert isinstance(res[game_id]['priority'], int)
        assert res[game_id]['priority'] == 8

    def test_write_db_full_rewrite(self, cm):
        game_id = 'CM10'  # Maui Mallard
        new_data = cm.read_db()
        new_data[game_id]['total_bits'] = 700

        for game in new_data:
            new_data[game]['priority'] = 11

        res = cm.write_db(new_data=new_data)

        assert isinstance(res, dict)
        assert isinstance(res[game_id], dict)
        assert isinstance(res[game_id]['total_bits'], int)
        assert res[game_id]['total_bits'] == 700
        assert isinstance(res[game_id]['game_name'], basestring)
        assert res[game_id]['game_name'] == 'Maui Mallard'
        assert isinstance(res[game_id]['priority'], int)
        assert res[game_id]['priority'] == 11

    def test_read_db(self, cm):
        game_id = 'CM22'  # Ball Jacks
        res = cm.read_db()
        assert isinstance(res, dict)
        assert isinstance(res[game_id], dict)
        assert isinstance(res[game_id]['total_bits'], int)
        assert isinstance(res[game_id]['game_name'], basestring)
        assert res[game_id]['game_name'] == 'Ball Jacks'
        assert isinstance(res[game_id]['priority'], int)

    def test_read_db_game_id(self, cm):
        game_id = 'CM8'  # Brett Hull Hockey 95
        res = cm.read_db(game_id=game_id)

        assert isinstance(res, dict)
        assert isinstance(res['total_bits'], int)
        assert isinstance(res['game_name'], basestring)
        assert res['game_name'] == 'Brett Hull Hockey 95'
        assert isinstance(res['priority'], int)

    def test_parse_chat_message_nope(self, cm):
        with pytest.raises(TypeError):
            cm.parse_chat_message()

        nope = cm.parse_chat_message(chat_message="GIT GUD KAPPA !!1!1")
        assert nope is None

        nope_again = cm.parse_chat_message(chat_message="GIT GUD CM !!1!1")
        assert nope_again is None

    def test_parse_chat_message_ok(self, cm):
        game_id_classic = cm.parse_chat_message(
            chat_message="Omg that baneling bust was Kreygasm CM16 cheer10 cheer10 cheer100")

        assert game_id_classic == 'CM16'

        game_id_upper_spaced = cm.parse_chat_message(
            chat_message="cheer500 Wow! What a Save! Siiick! CM 22")

        assert game_id_upper_spaced == 'CM22'

        game_id_lower = cm.parse_chat_message(
            chat_message="cheer200 Sed ut error sit voluptatem cm10")

        assert game_id_lower == 'CM10'

        game_id_lower_spaced = cm.parse_chat_message(
            chat_message="cheer1400 You should read that linked article more closely, PogChamp cm 17")

        assert game_id_lower_spaced == 'CM17'
