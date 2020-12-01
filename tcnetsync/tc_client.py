import time
import socket
from threading import Lock, Thread
import logging
import select

from timecode import Timecode

from tcnetsync.tc_sync import TcSync
from tcnetsync.tc_reader import TcReader


class TcSyncClient(TcSync):
    def __init__(self, host="127.0.0.1", port=9998, debug=False):
        super().__init__()
        self.host = host
        self.port = port
        self.lock = Lock()
        self.sock = None
        self.last_hb_resp = time.time()
        self.heartbeat_period = 10
        self.listener_thread = None
        self.running = False

    def start(self):
        self.setup_socket()
        self.request_sync()
        self.running = True
        self.listener_thread = Thread(target=self.listener)
        self.listener_thread.start()
        # self.listener()

    def stop(self):
        self.running = False
        self.sock.close()

    def setup_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket
        self.sock.setblocking(False)

    def request_sync(self):
        self.logger.info(f"Requesting sync...")
        self.sock.sendto(b"/sync/add", (self.host, self.port))

    def heartbeat(self):
        t = time.time()
        while True:
            if time.time() - t > self.heartbeat_period:
                self.sock.sendto(b"/heartbeat", (self.host, self.port))
                t = time.time()
            yield

    def handle_msg(self, msg):
        msg = msg.decode('utf-8')
        ts, fr, tc, factor = msg.split(",")
        tc = Timecode(int(fr), tc)
        jam_data = float(ts), tc, float(factor)
        with self.lock:
            self.update_sync(jam_data[0], jam_data[1])

    def listener(self):
        # timeout = 0.1 # Timeout to stop select blocking
        self.logger.info("Listening for sync messages...")
        hb = self.heartbeat()
        while self.running:
            next(hb)
            readable, writeable, error = select.select([self.sock], [self.sock], [], 0)
            for sock in readable:
                # print(ready)
                msg = sock.recvfrom(128)
                self.handle_msg(msg[0])
            time.sleep(0.01)



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    sync = TcSyncClient()
    tcr = TcReader(sync, freeroll=3)

    tcr.start()
    sync.start()


