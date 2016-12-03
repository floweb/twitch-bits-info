import logging

try:
    import thread
    import Tkinter as tk
    import ttk
    import ScrolledText as tkst
except ImportError:
    import _thread as thread
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.scrolledtext as tkst

from twitchbitsinfo import TwitchBitsInfo

logger = logging.getLogger('twitch_bits_info')


class CMTk(tk.Tk):
    def __init__(self, parent=None):
        tk.Tk.__init__(self, parent)
        self.parent = parent

        self.log_text = tkst.ScrolledText(self, state=tk.DISABLED)
        self.log_text.configure(font='TkFixedFont')
        self.log_text.pack(side=tk.LEFT, padx=5, pady=5)

        self.start_button = ttk.Button(parent, text='Start ConsoleMini', state=tk.NORMAL,
                                       command=self.start_twitch_bits_info)
        self.start_button.pack(side=tk.TOP, padx=12, pady=12)

        self.stop_button = ttk.Button(parent, text='Stop ConsoleMini', state=tk.DISABLED,
                                      command=self.stop_twitch_bits_info)
        self.stop_button.pack(side=tk.TOP, padx=12, pady=12)

        self.update_button = ttk.Button(parent, text='Manual update JSON', state=tk.DISABLED,
                                        command=self.manual_update_json)
        self.update_button.pack(side=tk.TOP, padx=12, pady=12)

    def manual_update_json(self):
        self.bits.cm.update_trending_games()

    def start_twitch_bits_info(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_button.config(state=tk.NORMAL)
        self.bits = TwitchBitsInfo()

        def run(*args):
            """
            Starts TwitchBitsInfo in another thread
            """
            self.bits.start()

        thread.start_new_thread(run, ())

    def stop_twitch_bits_info(self):
        # Shutdown Twitch API access etc...
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_button.config(state=tk.DISABLED)
        self.bits.shutdown()


class TextHandler(logging.StreamHandler):
    """
    This class allows you to log to a Tkinter Text or ScrolledText widget.
    """
    def __init__(self, text):
        # run the regular StreamHandler __init__
        logging.StreamHandler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state=tk.NORMAL)
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state=tk.DISABLED)

            # Autoscroll to the bottom
            self.text.yview(tk.END)

        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)

if __name__ == "__main__":
    # Create Tk object instance
    app = CMTk()
    app.title('ConsoleMini')

    # Create TextHandler
    text_handler = TextHandler(app.log_text)
    logger.addHandler(text_handler)
    logger.setLevel(logging.INFO)

    # Start Tk mainloop
    app.mainloop()
