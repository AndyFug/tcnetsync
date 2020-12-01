import logging

class TcBase:
    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)


class TcEvent(list):
    def __call__(self, *args, **kwargs):
        self.emit(*args, **kwargs)

    def connect(self, cb):
        self.append(cb)

    def emit(self, *args, **kwargs):
        for f in self:
            f(*args, **kwargs)

    def __repr__(self):
        return "Event(%s)" % list.__repr__(self)


class TcLoggerHandler(logging.Handler):

    def __init__(self, handler=None):
        super().__init__()
        self.handler = handler


    def emit(self, record):
        self.handler(self.format(record))
