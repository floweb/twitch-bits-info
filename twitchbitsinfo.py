from __future__ import print_function

try:
    import ConfigParser as configparser
    import thread
except ImportError:
    import configparser
    import _thread as thread
from datetime import datetime
import json
import logging
import os
import time
import webbrowser

import pytwitcherapi
import websocket

from consolemini import ConsoleMini


class TwitchLoginException(Exception):
    pass


class TwitchGetDataException(Exception):
    pass


class BadConfigurationException(Exception):
    def __init__(self, missing_param):
        message = "You must set a {} in your config.ini".format(missing_param)
        print(message)
        super(BadConfigurationException, self).__init__(message)


class TwitchBitsInfo(object):

    def __init__(self):
        config_dict = self._get_config()
        # We need to get a dict from the 'config' section of the config file,
        # to properly setup this class attributes like logs, etc...
        self.__dict__.update(config_dict)
        self._setup()

    def start(self):
        # Standard REST API:
        # This is use to get channel_id from a channel_name,
        # and the OAuth token needed for Websocket requests
        self.twitch = pytwitcherapi.TwitchSession()

        self.twitch_login()
        self.access_token = self.twitch.token['access_token']
        try:
            self.channel_id
        except AttributeError:
            self.channel_id = self.get_channel_id()
            self._write_config('channel_id', self.channel_id)

        if self.first_run:
            # First run was a success, we don't need to wait 45 seconds for user login
            # Set first_run param to 0 (== False)
            self._write_config('first_run', '0')

        # Websocket / PubSub:
        # This is use to get Twitch's Bits information stream
        if self.verbose:
            websocket.enableTrace(True)

        self.twitch.ws = websocket.WebSocketApp(
            self.ws_host,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=lambda _: self.log.info("Terminating...")
        )

        self.cm = ConsoleMini(db_filepath=self.db_filepath, log=self.log)

        self.twitch.ws.on_open = self.on_open
        self.twitch.ws.run_forever()

    def shutdown(self):
        self.log.critical('Waiting for threads to go away...')
        self.twitch.ws.close()

    def get_channel_id(self):
        try:
            return self.twitch.get_channel(self.channel_name).__dict__['twitchid']
        except:
            raise TwitchGetDataException

    def twitch_login(self):
        self.twitch.start_login_server()
        url = self.twitch.get_auth_url()
        webbrowser.open(url)

        if self.first_run:
            time.sleep(45)
        else:
            time.sleep(5)

        self.twitch.shutdown_login_server()

        self.log.info('Logged in as: {}'.format(self.twitch.current_user))
        self.log.debug('Using auth token: {}'.format(self.twitch.token['access_token']))
        return self.twitch.authorized

    def on_error(self, ws, error):
        self.log.critical(error)

    def on_message(self, ws, message):
        """
        This is a Bits event message example.

        {
            "type": "MESSAGE",
            "data": {
                "topic": "channel-bitsevents.<channel_id>",
                "message": {
                    "user_name": "dallasnchains",
                    "channel_name": "twitch",
                    "user_id": "...",
                    "channel_id": "...",
                    "time": "2015-12-19T16:39:57-08:00",
                    "chat_message": "Omg that baneling bust was Kreygasm CM16 cheer10 cheer10 cheer100",
                    "bits_used": 120,
                    "total_bits_used": 620,
                    "context": "cheer"
                }
            }
        }
        """
        message_dict = json.loads(message)
        self.log.debug('message_dict: {}'.format(str(message_dict)))

        if (message_dict['type'] == 'MESSAGE' and
           'channel-bitsevents' in message_dict['data']['topic']):

            message_data = json.loads(message_dict['data']['message'])
            self.log.debug('message_data: {}'.format(str(message_data)))

            # We got a new bits message... let's deal with it !
            # Do useful stuff, like update trending games for ConsoleMini
            self.log.info('New cheer from {} !'.format(message_data['user_name']))
            self.log.info('Message: {}'.format(message_data['chat_message']))
            self.log.info('Bits cheered: {}'.format(message_data['bits_used']))
            self.cm.update_trending_games(message_data['chat_message'], int(message_data['bits_used']))

    def on_open(self, ws):
        def run(*args):
            """
            send the sub message,
            and keep alive our connection to Twitch pubsub service
            """
            self.sub_to_bitsevents()
            self.keep_alive(ws)

        thread.start_new_thread(run, ())

    def keep_alive(self, ws):
        def alive(*args):
            """
            send the ping message,
            then wait 30 seconds and ping again...
            so thread doesn't exit and socket isn't closed
            """
            while True:
                self.ping()
                time.sleep(30)

        thread.start_new_thread(alive, ())

    def send_data(self, data):
        """
        ws.send wants a json object, and not a Python obj, we take care of that.
        """
        self.twitch.ws.send(json.dumps(data))

    def sub_to_bitsevents(self):
        data = {
            "type": "LISTEN",
            "data": {
                "topics": ["channel-bitsevents.{}".format(self.channel_id)],
                "auth_token": self.access_token,
            }
        }
        self.send_data(data)

    def ping(self):
        self.send_data({"type": "PING"})

    def _setup(self):
        try:
            self.twitch_client_id
        except AttributeError:
            BadConfigurationException('twitch_client_id')

        # pytwitcherapi.TwitchSession() fetch the Client ID from an envvar
        os.environ["PYTWITCHER_CLIENT_ID"] = self.twitch_client_id

        try:
            self.channel_name
        except AttributeError:
            BadConfigurationException('channel_name')

        try:
            self.db_filepath
        except AttributeError:
            BadConfigurationException('db_filepath')

        try:
            self.ws_host
        except AttributeError:
            self.ws_host = "wss://pubsub-edge.twitch.tv"

        try:
            self.first_run = bool(int(self.first_run))
        except AttributeError:
            self.first_run = True

        try:
            self.verbose = bool(int(self.verbose))
        except AttributeError:
            self.verbose = False

        self._setup_log(self.verbose)

    def _setup_log(self, verbose):
        self.log = logging.getLogger('twitch_bits_info')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        steam_handler = logging.StreamHandler()
        steam_handler.setFormatter(formatter)

        date_now = datetime.now().strftime("%Y-%m-%d")
        file_handler = logging.FileHandler(filename='{}.log'.format(date_now))
        file_handler.setFormatter(formatter)

        if verbose:
            self.log.setLevel(logging.DEBUG)
            steam_handler.setLevel(logging.DEBUG)
            file_handler.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.INFO)
            steam_handler.setLevel(logging.INFO)
            file_handler.setLevel(logging.INFO)

        self.log.addHandler(steam_handler)
        self.log.addHandler(file_handler)

        self.log.info('Starting app!')
        return self.log

    def _get_config(self):
        self.config = configparser.ConfigParser()
        self.config.readfp(open('config.ini', 'r'))

        return dict(self.config.items('config'))

    def _write_config(self, option, value):
        self.config.set('config', option, str(value))
        with open('config.ini', 'r+') as f:
            self.config.write(f)
