try:
    basestring
except NameError:
    basestring = str

import logging
import os
import shutil

import pytest

from consolemini import BadArgsException, ConsoleMini


def restore_base_data():
    """
    Revert consolemini.test.json to its original content.
    """

    db_dirname = os.path.dirname(os.path.realpath(__file__))
    shutil.copyfile(src=os.path.join(db_dirname, 'consolemini.base.json'),
                    dst=os.path.join(db_dirname, 'consolemini.test.json'))


# TODO:
# def pytest_generate_tests(metafunc):
#     if 'cm' in metafunc.fixturenames:
#         metafunc.parametrize("cm", ['api', 'no_api'], indirect=True)


@pytest.fixture(scope="module")
def cm(request):
    # dummy logger instance
    log = logging.getLogger()
    db_filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'consolemini.test.json')

    # TODO:
    # if request.param == "api":
    #     api_url = 'http://localhost:3000'
    #     api_key = r'hGC2&cC97#nE]|Sm_556623e"AUbA89SAwQEcTJ%gllLFen*0z6u61+b_9?Jn3k'
    #     cm = ConsoleMini(db_filepath=db_filepath, log=log, api_url=api_url, api_key=api_key)
    # else:

    cm = ConsoleMini(db_filepath=db_filepath, log=log)

    try:
        yield cm
    except:
        print(cm.read_db())

    # Revert consolemini.test.json to its original content
    restore_base_data()


@pytest.fixture(scope="module")
def trending_files():
    db_dirname = os.path.dirname(os.path.realpath(__file__))

    return [os.path.join(db_dirname, 'consolemini.1.txt'),
            os.path.join(db_dirname, 'consolemini.2.txt'),
            os.path.join(db_dirname, 'consolemini.3.txt')]


class TestConsoleMini:

    def test_write_db_nope(self, cm):
        with pytest.raises(BadArgsException):
            cm.write_db()

    def test_write_db_ok(self, cm):
        game_id = 'CM5'  # Fatal Rewind
        current_game = {"id": "CM5", "total_bits": 1200,
                        "game_name": "Fatal Rewind", "priority": 8}
        res = cm.write_db(game_id=game_id, current_game=current_game)

        assert isinstance(res, dict)
        assert isinstance(res['games'], list)

        res_game = [game
                    for game in res['games']
                    if game['id'] == game_id][0]

        assert isinstance(res_game, dict)
        assert isinstance(res_game['total_bits'], int)
        assert res_game['total_bits'] == 1200
        assert isinstance(res_game['game_name'], basestring)
        assert res_game['game_name'] == 'Fatal Rewind'
        assert isinstance(res_game['priority'], int)
        assert res_game['priority'] == 8

        # Revert consolemini.test.json to its original content
        restore_base_data()

    def test_write_db_full_rewrite(self, cm):
        game_id = 'CM10'  # Maui Mallard
        new_data = cm.read_db()

        # Just messing around with data...
        for index, _ in enumerate(new_data['games']):
            new_data['games'][index]['priority'] = 11
            if new_data['games'][index]['id'] == game_id:
                new_data['games'][index]['total_bits'] = 700

        res = cm.write_db(new_data=new_data)

        assert isinstance(res, dict)
        assert isinstance(res['games'], list)

        res_game = [game
                    for game in res['games']
                    if game['id'] == game_id][0]

        assert isinstance(res_game, dict)
        assert isinstance(res_game['total_bits'], int)
        assert res_game['total_bits'] == 700
        assert isinstance(res_game['game_name'], basestring)
        assert res_game['game_name'] == 'Maui Mallard'
        assert isinstance(res_game['priority'], int)
        assert res_game['priority'] == 11

        # Revert consolemini.test.json to its original content
        restore_base_data()

    def test_read_db(self, cm):
        game_id = 'CM22'  # Ball Jacks
        res = cm.read_db()
        assert isinstance(res, dict)
        res_game = [game
                    for game in res['games']
                    if game['id'] == game_id][0]

        assert isinstance(res_game, dict)
        assert isinstance(res_game['total_bits'], int)
        assert isinstance(res_game['game_name'], basestring)
        assert res_game['game_name'] == 'Ball Jacks'
        assert isinstance(res_game['priority'], int)

    def test_read_db_game_id(self, cm):
        game_id = 'CM8'  # Brett Hull Hockey 95
        res_game = cm.read_db(game_id=game_id)

        assert isinstance(res_game, dict)
        assert isinstance(res_game['total_bits'], int)
        assert isinstance(res_game['game_name'], basestring)
        assert res_game['game_name'] == 'Brett Hull Hockey 95'
        assert isinstance(res_game['priority'], int)

    def test_read_db_game_id_nope(self, cm):
        game_id = 'CM1337'  # NOPE !!!
        res = cm.read_db(game_id=game_id)
        assert res is None

    def test_parse_chat_message_nope(self, cm):
        with pytest.raises(TypeError):
            cm.parse_chat_message()

        nope = cm.parse_chat_message(chat_message="GIT GUD KAPPA !!1!1")
        assert nope is None

        nope_again = cm.parse_chat_message(chat_message="GIT GUD CM !!1!1")
        assert nope_again is None

        with pytest.raises(AttributeError):
            cm.parse_chat_message(chat_message={'toto': 'whoops'})

        with pytest.raises(AttributeError):
            cm.parse_chat_message(chat_message=[1, 2, 3])

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

    def test_write_trending_files_nope(self, cm):
        with pytest.raises(TypeError):
            cm.write_trending_files()

        with pytest.raises(TypeError):
            cm.write_trending_files(trending_games={'toto': 'whoops'})

        with pytest.raises(TypeError):
            cm.write_trending_files(trending_games=[1, 2, 3])

        with pytest.raises(TypeError):
            cm.write_trending_files(trending_games='1, 2, 3')

    def _write_trending_files_ok(self, cm, trending_files, remove):
        if remove:
            for trending_file in trending_files:
                os.remove(trending_file)

        trending_games = [{'total_bits': 300, 'game_name': 'Kid Chameleon', 'priority': 9},
                          {'total_bits': 300, 'game_name': 'Rocket Knight Adventures', 'priority': 10},
                          {'total_bits': 100, 'game_name': 'Ecco', 'priority': 10}]
        cm.write_trending_files(trending_games=trending_games)

        for index, trending_file in enumerate(trending_files):
            with open(trending_file) as f:
                if index == 0:
                    assert f.read() == 'Kid Chameleon : 300 bits'
                if index == 1:
                    assert f.read() == 'Rocket Knight Adventures : 300 bits'
                if index == 2:
                    assert f.read() == 'Ecco : 100 bits'

    def test_write_trending_files_ok(self, cm, trending_files):
        self._write_trending_files_ok(cm, trending_files, remove=False)

    def test_write_trending_files_ok_remove(self, cm, trending_files):
        self._write_trending_files_ok(cm, trending_files, remove=True)

    def test_reset_priority_nope(self, cm):
        with pytest.raises(TypeError):
            cm.reset_priority()

        with pytest.raises(TypeError):
            cm.reset_priority(cm_data={'toto': 'whoops'})

        with pytest.raises(TypeError):
            cm.reset_priority(cm_data=[1, 2, 3])

        with pytest.raises(TypeError):
            cm.reset_priority(cm_data='1, 2, 3')

        with pytest.raises(KeyError):
            cm.reset_priority(cm_data={'toto': 'whoops'}, total_bits={'toto': 'whoops'})

        with pytest.raises(TypeError):
            cm.reset_priority(cm_data=[1, 2, 3], total_bits=[1, 2, 3])

        with pytest.raises(TypeError):
            cm.reset_priority(cm_data='1, 2, 3', total_bits='1, 2, 3')

    def test_reset_priority_ok(self, cm):
        cm_data = cm.read_db()
        total_bits = 200
        # These games have total_bits == 200, they should have priority == 10
        games_to_test = ['CM8', 'CM16', 'CM28']

        new_data = cm.reset_priority(cm_data=cm_data, total_bits=total_bits)

        res_games = [game
                     for game in new_data['games']
                     if game['id'] in games_to_test]

        for game in res_games:
            assert game['priority'] == 10

    def test_reset_priority_returns_none(self, cm):
        cm_data = cm.read_db()

        # In our test.json, none of the games already have total_bits == 400
        # In this particular case, reset_priority() should return None
        total_bits = 400
        this_should_be_none = cm.reset_priority(cm_data=cm_data, total_bits=total_bits)
        assert this_should_be_none == cm_data

    def test_update_trending_games_nope(self, cm):
        nope = cm.update_trending_games(chat_message=1)
        assert nope is False

        with pytest.raises(AttributeError):
            cm.update_trending_games(chat_message=1, bits_used=1)

        nope = cm.update_trending_games(chat_message="chat_message", bits_used="bits_used")
        assert nope is False

        nope_nope = cm.update_trending_games(chat_message={'toto': 'whoops'})
        assert nope_nope is False

        nope_nope_nope = cm.update_trending_games(chat_message='1, 2, 3', bits_used='1, 2, 3')
        assert nope_nope_nope is False

        with pytest.raises(AttributeError):
            cm.update_trending_games(chat_message={'toto': 'whoops'}, bits_used={'toto': 'whoops'})

        with pytest.raises(AttributeError):
            cm.update_trending_games(chat_message=[1, 2, 3], bits_used=[1, 2, 3])

    def test_update_trending_games_update_files_only(self, cm, trending_files):
        update = cm.update_trending_games()
        assert update is True

        for index, trending_file in enumerate(trending_files):
            with open(trending_file) as f:
                if index == 0:
                    assert f.read() == 'Kid Chameleon : 1600 bits'
                if index == 1:
                    assert f.read() == 'Pete Sampras : 1400 bits'
                if index == 2:
                    assert f.read() == 'Maui Mallard : 1400 bits'

    def test_update_trending_games_ok(self, cm, trending_files):
        ok_update_cm16 = cm.update_trending_games(
            chat_message="Omg that baneling bust was Kreygasm CM16 cheer10 cheer10 cheer100",
            bits_used=120)
        assert ok_update_cm16 is True

        for index, trending_file in enumerate(trending_files):
            with open(trending_file) as f:
                if index == 0:
                    assert f.read() == 'Kid Chameleon : 1600 bits'
                if index == 1:
                    assert f.read() == 'Pete Sampras : 1400 bits'
                if index == 2:
                    assert f.read() == 'Maui Mallard : 1400 bits'

        ok_update_cm10 = cm.update_trending_games(
            chat_message="cheer2200 Sed ut error sit voluptatem cm10",
            bits_used=2200)
        assert ok_update_cm10 is True

        for index, trending_file in enumerate(trending_files):
            with open(trending_file) as f:
                if index == 0:
                    assert f.read() == 'Maui Mallard : 3600 bits'
                if index == 1:
                    assert f.read() == 'Kid Chameleon : 1600 bits'
                if index == 2:
                    assert f.read() == 'Pete Sampras : 1400 bits'

        ok_update_cm_10 = cm.update_trending_games(
            chat_message="cheer500 Sed ut error sit voluptatem cm 10",
            bits_used=500)
        assert ok_update_cm_10 is True

        for index, trending_file in enumerate(trending_files):
            with open(trending_file) as f:
                if index == 0:
                    assert f.read() == 'Maui Mallard : 4100 bits'
                if index == 1:
                    assert f.read() == 'Kid Chameleon : 1600 bits'
                if index == 2:
                    assert f.read() == 'Pete Sampras : 1400 bits'

        ok_update_cm_22 = cm.update_trending_games(
            chat_message="cheer500 Wow! What a Save! Siiick! CM 22",
            bits_used=500)
        assert ok_update_cm_22 is True

        for index, trending_file in enumerate(trending_files):
            with open(trending_file) as f:
                if index == 0:
                    assert f.read() == 'Maui Mallard : 4100 bits'
                if index == 1:
                    assert f.read() == 'Kid Chameleon : 1600 bits'
                if index == 2:
                    assert f.read() == 'Pete Sampras : 1400 bits'

        ok_update_cm_17 = cm.update_trending_games(
            chat_message="cheer1400 You should read that linked article more closely, PogChamp cm 17",
            bits_used=1400)
        assert ok_update_cm_17 is True

        for index, trending_file in enumerate(trending_files):
            with open(trending_file) as f:
                if index == 0:
                    assert f.read() == 'Maui Mallard : 4100 bits'
                if index == 1:
                    assert f.read() == 'Pete Sampras : 2800 bits'
                if index == 2:
                    assert f.read() == 'Kid Chameleon : 1600 bits'

        # Bug found by monsieursapin
        ok_update_cm6 = cm.update_trending_games(
            chat_message="cheer300 cm6",
            bits_used=300)
        assert ok_update_cm6 is True

        for index, trending_file in enumerate(trending_files):
            with open(trending_file) as f:
                if index == 0:
                    assert f.read() == 'Maui Mallard : 4100 bits'
                if index == 1:
                    assert f.read() == 'Pete Sampras : 2800 bits'
                if index == 2:
                    assert f.read() == 'Kid Chameleon : 1600 bits'
