import logging

from tcnetsync import tc_server, tc_client, tc_reader

# Set root logger
logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)

# Setup server, client and reader
server = tc_server.MTCServer()
client = tc_client.TcSyncClient()
reader = tc_reader.TcReader(client, freeroll=3)

# server.logger.setLevel(logging.DEBUG)
# client.logger.setLevel(logging.DEBUG)

server.start()
client.start()
reader.start()  # NB: Reader doesn't display in Pycharm