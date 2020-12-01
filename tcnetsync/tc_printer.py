import time, sys


class TCPrinter:
    def __init__(self):
        self.last_msg = 0
        self.msg_duration = 0.5
        self.message = ""

    def print(self, tc):
        if time.time() - self.last_msg > self.msg_duration:
            self.message = "        "

        text = f"\t{str(tc)} \t{self.message}"

        # sys.stdout.write("\r" + text + "\r")
        print('\r' + text, end="\r")  # Doesn't work in Pycharm
        # sys.stdout.flush()

    def msg(self, msg):
        self.message = msg
        self.last_msg = time.time()