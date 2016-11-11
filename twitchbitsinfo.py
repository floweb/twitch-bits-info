import json
import os
try:
    import thread
except ImportError:
    import _thread as thread
import time
import webbrowser

import pytwitcherapi
import websocket


class TwitchLoginException(Exception):
    pass


class TwitchGetDataException(Exception):
    pass


class TwitchBitsInfo(object):

    def __init__(self, host=None, channel_name=None):
        """
        """
        if not host:
            self.host = "wss://pubsub-edge.twitch.tv"

        if not channel_name:
            self.channel_name = "monsieursapin"
            # self.channel_name = "kraken"

        # Standard REST API:
        # This is used to get channel_id from a channel_name,
        # and the auth token needed for the Websocket requests
        os.environ['PYTWITCHER_CLIENT_ID'] = 'bc4ozy62dshy18hq1wp8nrhfz44rknd'
        self.ts = pytwitcherapi.TwitchSession()

        self.twitch_login()
        self.current_twitch_user = self.ts.current_user
        self.channel_id = self.get_channel_id()

        # Websocket / PubSub:
        # This is used to get Twitch's Bits information stream
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            self.host,
            on_message=self.on_message, on_error=self.on_error,
            on_close=lambda ws: print("### closed ###"))

        self.ws.on_open = self.on_open
        self.ws.run_forever()

    def close(self):
        self.ws.close()

    def get_channel_id(self):
        try:
            return self.ts.get_channel(self.channel_name).__dict__['twitchid']
        except:
            raise TwitchGetDataException

    def twitch_login(self):
        self.ts.start_login_server()

        url = self.ts.get_auth_url()
        webbrowser.open(url)
        input("Press ENTER when finished")

        self.ts.shutdown_login_server()
        return self.ts.authorized

    def on_error(self, ws, error):
        print(error)

    def on_message(self, ws, message):
        """
        This is a Bits event message example.

        {
            "type": "MESSAGE",
            "data": {
                "topic": "channel-bitsevents.XXXXXXXX",
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
        print(message)

    def on_open(self, ws):
        def run(*args):
            """
            send the message,
            then wait,
            so thread doesn't exit and socket isn't closed
            """
            self.sub_to_bits_topic()
            time.sleep(1)

        thread.start_new_thread(run, ())

    def send_data(self, data):
        """
        ws.send wants a json object, and not a Python obj, we take care of that.
        """
        self.ws.send(json.dumps(data))

    def sub_to_bits_topic(self):
        data = {
            "type": "LISTEN",
            "data": {
                "topics": ["channel-bitsevents.{}".format(self.channel_id)],
                "auth_token": "...",
            }
        }
        self.send_data(data)

    def ping(self):
        data = {
            "type": "PING"
        }
        self.send_data(data)
