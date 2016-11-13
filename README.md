# Twitch Bits Info

Messing around with twitch APIs and Websockets for fun and ... proBits.

This is still a big juicy **WIP**.

## How to use

Firstly, you have to declare your own app in your Twitch account.
- Go [there](https://www.twitch.tv/settings/connections) and click the `Register your application` button at the bottom of the page, and write down your Client ID **somewhere SAFE**.
- `git  clone https://github.com/floweb/twitch-bits-info`
- `cd twitch-bits-info`
- `pip install -r requirements.txt`
- `cp config.example.ini config.ini`
- Edit this new file with your stuff, like the Client ID we talked before.
- Launch `python app.py`, and that's all... You can stop it with a simple Ctrl+C.

I'm trying my best to make it compatible with Python 2.7+ & 3, but **seriously use Python 3**.