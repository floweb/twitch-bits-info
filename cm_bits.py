from twitchbitsinfo import TwitchBitsInfo

if __name__ == "__main__":
    try:
        ws = TwitchBitsInfo()
    except KeyboardInterrupt:
        ws.close()
        print("Terminating...")
