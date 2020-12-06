import logging

from tcnetsync import tc_server, tc_client, tc_reader

# logging.basicConfig(level=logging.DEBUG)

# Setup server, client and reader
server = tc_server.MTCServer()
client = tc_client.TcSyncClient()
reader = tc_reader.TcReader(client, freeroll=3)

server.start()
client.start()
reader.start()  # NB: Reader doesn't display in Pycharm