from twitchbitsinfo import TwitchBitsInfo

if __name__ == "__main__":
    try:
        bits = TwitchBitsInfo()
    except KeyboardInterrupt:
        bits.close()
