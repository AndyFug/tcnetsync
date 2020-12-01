from timecode import Timecode
import time
from tcnetsync.tcbase import TcBase, TcEvent
from tcnetsync.mtc import MTCParser
import mido


def secs_to_hms(secs):
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    return "{:02d}:{:02d}:{}".format(int(h), int(m), s)


class TcSync(TcBase):
    def __init__(self):
        super().__init__()
        self.freeroll = 5  # If freeroll is negative, infinite freeroll

        self.tc_start_pos = 0  # Start position of timecode (eg 01:00:00:00) in secs
        self.tc_start_ts = time.time()  # Timestamp of start timecode position

        self.last_ts = time.time() - self.freeroll  # Last timecode sync timestamp
        self.last_tc = Timecode(25)  # Last timecode sync position (TC object)

        self.newSyncEvent = TcEvent()  # New timecode sync event (eg... when timecode jumps to new position)
        self.syncUpdateEvent = TcEvent()  # Event for when the sync has been updated (re-synced)

    def new_sync(self, sync_ts, sync_tc):
        self.logger.info(f"NEW SYNC: {sync_tc} {sync_tc.framerate}fps")
        sync_tc_pos = sync_tc.frame_number / int(sync_tc.framerate)
        self.tc_start_ts = sync_ts
        self.tc_start_pos = sync_tc_pos

        self.last_ts = sync_ts
        self.last_tc = sync_tc

        self.newSyncEvent()

    def update_sync(self, sync_ts: float, sync_tc: Timecode):
        # print("Updating sync")
        if self.is_new_sync(sync_ts, sync_tc):
            self.new_sync(sync_ts, sync_tc)
        else:
            self.last_ts = sync_ts
            self.last_tc = sync_tc

            self.syncUpdateEvent()

    # Checks to determine if the sync is a new sequence
    def is_new_sync(self, jam_ts: float, jam_tc: Timecode):
        tc_pos = jam_tc.frame_number / int(jam_tc.framerate)
        # Check TC direction
        if tc_pos - self.last_tc_pos <= 0:
            return True
        # Check if we've exceeded freeroll time
        if self.freeroll_exceeded(jam_ts):
            return True
        # Check for different framerate
        if int(jam_tc.framerate) != self.fr:
            self.logger.debug("DIFFERENT FRAMERATE")
            return True
        # Check for jump
        if self.is_tc_jump(jam_tc, jam_ts):
            return True
        return False

    # Check if new TC value is a jump from current value
    def is_tc_jump(self, tc, ts):
        tc_pos_diff = (tc.frame_number - self.last_tc.frame_number)/int(tc.framerate)
        ts_diff = ts - self.last_ts
        if abs(tc_pos_diff - ts_diff) > 1:
            self.logger.debug(f"TIMECODE JUMP: {round(tc_pos_diff)}secs")
            return True

    @property
    def elapsed(self):
        return self.last_ts - self.tc_start_ts

    @property
    def elapsed_pos(self):
        return self.last_tc_pos - self.tc_start_pos

    @property
    def factor(self):
        if self.elapsed == 0 or self.elapsed_pos == 0:
            return 1
        else:
            return self.elapsed_pos / self.elapsed

    @property
    def fr(self):
        return int(self.last_tc.framerate)

    @property
    def last_tc_pos(self):
        return self.last_tc.frame_number / self.fr

    def freeroll_exceeded(self, ts):
        if self.freeroll < 0:
            return False
        else:
            result = ts - self.last_ts > self.freeroll
            if result:
                # print("FREEROLL EXCEEDED")
                pass
            return result

    def next_position(self, now):
        pos = ((now - self.tc_start_ts) * self.factor) + self.tc_start_pos
        return pos, self.fr


class MTCSync(TcSync):
    def __init__(self, midi_port=None):
        super().__init__()
        self.midi = midi_port
        self.new_sync_flag = False
        self.mtc_recv_thread = None
        self.running = False
        self.mtcparser = None

    def start(self, midi_port=None):
        self.midi = midi_port
        self.running = True
        self.mtc_recv()

    def stop(self):
        self.running = False
        if self.mtcparser:
            self.mtcparser.stop()
        self.logger.info("Finished receiving MTC.  Midi port closed")

    def handle_tc(self, tc, t):
        if tc is None:
            return
        now = t
        # Determine if this is a new sync
        if self.is_new_sync(now, tc):
            self.new_sync(now, tc)

        else:
            # Else... just update sync
            self.update_sync(now, tc)

    def mtc_recv(self):
        self.mtcparser = MTCParser(self.midi)
        self.mtcparser.listen(self.handle_tc)

    def midi_ports(self):
        return mido.get_input_names()