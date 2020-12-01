from threading import Thread, Lock
from timecode import Timecode
from tcnetsync.tc_sync import secs_to_hms
from tcnetsync.tc_printer import TCPrinter
import time

class TcReader:
    def __init__(self, sync, freeroll=5):
        self.pos = 0
        self.sync = sync
        self.gen_thread = Thread(target=self.gen)
        self.lock = Lock()
        self.fr = self.sync.fr

        self.sync.freeroll = freeroll  #If freeroll is negative, it will run forever
        self.running = False

    def start(self):
        self.running = True
        self.gen_thread.start()
        # self.sync.start()

    def current(self):
        tc = Timecode(self.sync.fr, secs_to_hms(self.pos))
        tc.set_fractional(False)
        return tc

    def gen(self):
        printer = TCPrinter()
        while self.running:
            now = time.time()
            if self.sync.freeroll_exceeded(now):
                time.sleep(0.1)
                continue

            with self.lock:
                self.pos, self.fr = self.sync.next_position(now)
                printer.print(self.current())
            time.sleep(1/self.fr)