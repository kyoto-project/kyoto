import beretta
import termformat


import kyoto.conf
import kyoto.utils.berp
import kyoto.network.stream
import kyoto.network.connection


class Service(object):

    def __init__(self, address, name):
        self.address = address
        self.name = name
        self.connections = kyoto.conf.settings.CONNECTION_MANAGER_CLASS(self.address)

    def send_message(self, connection, message):
        message = kyoto.utils.berp.pack(beretta.encode(message))
        return connection.sendall(message)

    def request(self, rtype, function, args, kwargs):
        connection = self.connections.acquire()
        status = self.send_message(connection, (rtype, self.name, function, args))
        stream = kyoto.network.stream.receive(connection, server=False)
        response = beretta.decode(next(stream))
        rtype = response[0]
        if rtype == ":reply":
            return response[1]
        elif rtype == ":noreply":
            return None
        else:
            raise NotImplementedError
        self.connections.release(connection)

    def call(self, function, args, **kwargs):
        return self.request(":call", function, args, kwargs)

    def cast(self, function, args, **kwargs):
        return self.request(":cast", function, args, kwargs)
