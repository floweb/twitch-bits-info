from __future__ import print_function

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

from twitchbitsinfo import TwitchBitsInfo

if __name__ == "__main__":
    config = configparser.ConfigParser()
    try:
        config.readfp(open('config.ini'))
        config_dict = {s: dict(config.items(s)) for s in config.sections()}
    except FileNotFoundError:
        print('WARNING: config.ini file does not exist, using default config values !')
        config_dict = {'config': {}}

    try:
        bits = TwitchBitsInfo(**config_dict['config'])
    except KeyboardInterrupt:
        bits.close()
