import json
import logging
import os
try:
    import thread
except ImportError:
    import _thread as thread
import time
import webbrowser

import pytwitcherapi
import websocket

try:
    input = raw_input  # Fix PY2
except NameError:
    pass


class TwitchLoginException(Exception):
    pass


class TwitchGetDataException(Exception):
    pass


class BadConfigurationException(Exception):
    def __init__(self, missing_param, logger):
        message = "You must set a {} in your config.ini".format(missing_param)
        logger.critical(message)
        super(BadConfigurationException, self).__init__(message)


class TwitchBitsInfo(object):

    def __init__(self, **kwargs):
        # Setup this class attributes, logs, etc...
        self.__dict__.update(kwargs)
        self._setup()

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

        self.twitch.ws.on_open = self.on_open
        self.twitch.ws.run_forever()

    def close(self):
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

        input("Press ENTER when your Twitch account is connected and PyTwitcher is authorized.")

        self.twitch.shutdown_login_server()

        if self.verbose:
            self.log.debug('Login with {} account, using auth token: {}'.format(
                self.twitch.current_user, self.twitch.token['access_token']))
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
                    "chat_message": "Omg that baneling bust was Kreygasm cheer10 cheer10 cheer100",
                    "bits_used": 120,
                    "total_bits_used": 620,
                    "context": "cheer"
                }
            }
        }
        """
        message_dict = json.loads(message)
        self.log.debug(message_dict)

        if message_dict['type'] == 'MESSAGE':
            # TODO: Do useful stuff
            self.log.info(message_dict['chat_message'])
            self.log.info(message_dict['user_name'])

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
            self.ws_host
        except AttributeError:
            self.ws_host = "wss://pubsub-edge.twitch.tv"

        try:
            self.verbose
        except AttributeError:
            self.verbose = False

        self.log = self._setup_log(self.verbose)

    def _setup_log(self, verbose):
        log = logging.getLogger(__name__)
        steam_handler = logging.StreamHandler()

        if verbose:
            log.setLevel(logging.DEBUG)
            steam_handler.setLevel(logging.DEBUG)
        else:
            log.setLevel(logging.INFO)
            steam_handler.setLevel(logging.INFO)

        log.addHandler(steam_handler)
        return log
