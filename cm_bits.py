import os

from twitchbitsinfo import TwitchBitsInfo

os.environ["PYTWITCHER_CLIENT_ID"] = 'bc4ozy62dshy18hq1wp8nrhfz44rknd'

if __name__ == "__main__":
    try:
        bits = TwitchBitsInfo()
    except KeyboardInterrupt:
        bits.close()
        bits.log.info("Terminating...")
