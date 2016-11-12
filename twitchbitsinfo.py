import json
import logging
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


class TwitchBitsInfo(object):

    def __init__(self, **kwargs):
        """
        """
        self.__dict__.update(kwargs)
        # Setup this class attributes, logs, etc...
        self.setup()

        # Standard REST API:
        # This is use to get channel_id from a channel_name,
        # and the OAuth token needed for Websocket requests
        self.twitch = pytwitcherapi.TwitchSession()

        self.twitch_login()
        self.current_twitch_user = self.twitch.current_user
        self.channel_id = self.get_channel_id()
        self.access_token = self.twitch.token['access_token']

        # Websocket / PubSub:
        # This is use to get Twitch's Bits information stream
        if self.verbose:
            websocket.enableTrace(True)

        self.twitch.ws = websocket.WebSocketApp(
            self.ws_host,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=lambda ws: self.log.info("### closed ###")
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

        input("Press ENTER when finished")

        self.twitch.shutdown_login_server()

        if self.verbose:
            self.log.debug(self.access_token)
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
        self.log.info(message)

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

    def setup(self):
        try:
            self.ws_host
        except AttributeError:
            self.ws_host = "wss://pubsub-edge.twitch.tv"

        try:
            self.channel_name
        except AttributeError:
            self.channel_name = "floweb"

        try:
            self.verbose
        except AttributeError:
            self.verbose = False

        self.log = self.setup_log(self.verbose)

    def setup_log(self, verbose):
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
