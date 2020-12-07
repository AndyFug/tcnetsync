import time
from threading import Thread
import socket
import select
from queue import Queue
import logging

from tcnetsync.tcbase import TcEvent, TcBase
from tcnetsync.tc_sync import MTCSync
from tcnetsync.tc_reader import TcReader


class BaseServer(TcBase):
    def __init__(self, interface="0.0.0.0", port=9998):
        super().__init__()
        self.port = port
        self.interface = interface
        self.sock = None

        self.clients = {}
        self.send_q = Queue()

        self.running = False
        self.server_thread = None
        self.ready_flag = True

        self.newClientEvent = TcEvent()
        self.clientRemovedEvent = TcEvent()
        self.clientsClearedEvent = TcEvent()

    def start(self, interface="0.0.0.0", port=9998):
        self.interface = interface
        self.port = port
        self.server_thread = Thread(target=self.server)
        self.running = True
        self.server_thread.start()

    def stop(self):
        self.running = False
        self.logger.info("Server stopped")

    def server(self):
        try:
            self.sock = socket.socket(socket.AF_INET,  # Internet
                                      socket.SOCK_DGRAM)  # UDP
            self.sock.setblocking(False)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.interface, self.port))
        except socket.error as e:
            self.logger.error(f"Error creating socket: {e}")
            self.stop()

        self.logger.info(f"UDP Server started.  Listening on port: {self.port}")

        # TODO: Make more efficient/elegant
        while self.running:
            self.remove_old_clients()
            # Send messages from send queue
            self.send_msgs()
            readable, writeable, errors = select.select([self.sock], [], [], 0)
            # print(readable)
            for sock in readable:
                try:
                    d = sock.recvfrom(128)
                    self.handle_msg(d)
                except socket.error as e:
                    self.logger.error(e)
            time.sleep(0.05)

        self.remove_clients()
        self.sock.close()
        self.logger.debug(f"Socket closed")

    def remove_old_clients(self):
        # Identify clients that haven't sent a heartbeat for a while
        now = time.time()
        remove = set()
        for c, hb_ts in self.clients.items():
            if now - hb_ts > 20:
                remove.add(c)

        for c in remove:
            self.remove_client(c)

    def add_client(self, client):
        self.logger.info(f"New client connection from: {client}")
        self.clients[client] = time.time()
        self.newClientEvent.emit(client)

    def remove_client(self, client):
        self.logger.info(f"Removing client connection: {client}")
        self.clients.pop(client)
        if not self.clients:
            self.logger.info("No clients connected.  Waiting for new client connections...")
        self.clientRemovedEvent.emit(client)

    def remove_clients(self):
        self.clients = {}
        self.logger.debug("Client list cleared")
        self.clientsClearedEvent.emit()

    def handle_heartbeat(self, client):
        now = time.time()
        if client not in self.clients:
            self.add_client(client)
        self.clients[client] = now
        # self.logger.debug(f"Heartbeat from: {client}")
        # self.heartbeat_reply(client)

    def heartbeat_reply(self, client):
        self.add_to_send_queue("HB REPLY", client)

    def add_to_send_queue(self, msg, client):
        msg_pkg = (msg, (client[0], client[1]))
        self.send_q.put(msg_pkg)

    def send_msgs(self):
        while self.send_q.qsize() > 0:
            msg_pkg = self.send_q.get()
            self.send_msg(msg_pkg[0], msg_pkg[1])

    def send_msg(self, msg: str, client):
        try:
            self.sock.sendto(msg.encode('utf-8'), client)
            self.logger.debug(f"MSG SENT: {msg} {client}")
        except socket.error as e:
            self.logger.error(f"There was a socket error while attempting to send a message: {e}")

    def handle_msg(self, d):
        msg = d[0].decode()
        client = d[1]
        self.logger.debug(f"MSG RECV: {client} {msg}")

        if msg == "/sync/add" or client not in self.clients:
            self.add_client(client)
        elif msg == "/sync/remove":
            self.remove_client(client)
        elif msg == "/heartbeat":
            self.handle_heartbeat(client)
        else:
            self.logger.error(f"UNHANDLED MESSAGE: {client} {msg}")


class MTCServer(BaseServer):
    def __init__(self, interface="0.0.0.0", port=9998, midi_port=None):
        super().__init__(interface, port)
        self.sync = MTCSync(midi_port=midi_port)
        self.last_send = 0
        self.new_sync_flag = True
        self.setup_callbacks()

    def start(self, interface="0.0.0.0", port=9998, midi_port=None):
        super().start(interface, port)
        self.sync.start(midi_port)

    def stop(self):
        super().stop()
        self.sync.stop()

    def setup_callbacks(self):
        self.sync.newSyncEvent.connect(self.handle_new_sync)
        self.sync.syncUpdateEvent.connect(self.handle_sync_update)

    def handle_new_sync(self):
        self.new_sync_flag = True
        self.update_clients()

    def handle_sync_update(self):
        self.update_clients()

    def current_tc(self):
        return self.sync.last_tc

    def update_clients(self):
        # If we don't have any clients, no point continuing
        if not self.clients:
            return

        # Send sync right away if it's a new sync
        if self.new_sync_flag:
            self.prepare_sync_message()
            self.new_sync_flag = False

        # Or send the sync if the last sync was sent >= 2 secs ago
        elif self.sync.last_ts - self.last_send >= 2:
            self.prepare_sync_message()

    def prepare_sync_message(self):
        msg = f"{str(self.sync.last_ts)},{str(self.sync.fr)},{str(self.sync.last_tc)}, {self.sync.factor}"
        msg = f"sync/update/{msg}"

        for c, ts in self.clients.items():
            self.add_to_send_queue(msg, c)

        self.last_send = self.sync.last_ts


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    server = MTCServer()
    server.start()
    tcr = TcReader(server.sync, freeroll=3)
    tcr.start()
