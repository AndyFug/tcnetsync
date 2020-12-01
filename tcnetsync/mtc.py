import time
import mido

from tcnetsync import tc_tools as tools
from tcnetsync.tcbase import TcBase


class MTCParser(TcBase):
    def __init__(self, port_name=None):
        super().__init__()
        self.qf_count = 0
        self.qf = [0, 0, 0, 0, 0, 0, 0, 0]
        self.port = mido.open_input(port_name)
        self.callbacks = set()

    def decode_mtc(self, message):
        t = time.time()

        if message.type == 'quarter_frame':
            # Make sure we have enough QFs to give full TC value
            self.qf_count += 1
            self.qf[message.frame_type] = message.frame_value
            if message.frame_type == 7 and self.qf_count > 7:
                tc = tools.mtc_decode_quarter_frames(self.qf)
                # print('QF:', tc)
                self.call_callbacks(tc, t)

        elif message.type == 'sysex':
            # check to see if this is a timecode frame
            if len(message.data) == 8 and message.data[0:4] == (127, 127, 1, 1):
                data = message.data[4:]
                tc = tools.mtc_decode(data)
                self.qf_count = 0
                print('FF:', tc)
                self.call_callbacks(tc, t)
        else:
            # print(message)
            pass

    def call_callbacks(self, tc, t):
        for c in self.callbacks:
            c(tc, t)

    def add_callback(self, cb):
        self.callbacks.add(cb)

    def remove_callbacks(self):
        self.callbacks.clear()

    def listen(self, cb):
        self.add_callback(cb)
        self.port.callback = self.decode_mtc
        self.logger.info('Listening to MIDI messages on > {} <'.format(self.port))

    def stop(self):
        self.port.close()
        self.remove_callbacks()
