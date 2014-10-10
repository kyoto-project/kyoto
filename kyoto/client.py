import beretta
import termformat


import kyoto.conf
import kyoto.utils.berp
import kyoto.network.stream
import kyoto.network.connection


class Service(object):

    def __init__(self, address, name):
        self.address = address
        if not termformat.is_atom(name):
            message = "Module name must be an atom '{0}' ~> '{1}'"
            name_as_atom = termformat.binary_to_atom(name)
            raise ValueError(message.format(name, name_as_atom))
        self.name = name
        self.connections = kyoto.conf.settings.CONNECTION_MANAGER_CLASS(self.address)

    def send_message(self, connection, message):
        message = kyoto.utils.berp.pack(beretta.encode(message))
        return connection.sendall(message)

    def request(self, rtype, function, args, kwargs):
        stream = kwargs.get("stream", None)
        connection = self.connections.acquire()
        if stream:
            response = self.stream_request(connection, rtype, function, args, stream)
        else:
            connection = self.connections.acquire()
            status = self.send_message(connection, (rtype, self.name, function, args))
            stream = kyoto.network.stream.receive(connection, server=False)
            response = self.handle_response(stream)
        self.connections.release(connection)
        return response

    def stream_request(self, connection, rtype, function, args, stream):
        status = self.send_message(connection, (":info", ":stream", []))
        status = self.send_message(connection, (rtype, self.name, function, args))
        stream = kyoto.network.stream.send(stream)
        for chunk in stream:
            connection.sendall(chunk)
        stream = kyoto.network.stream.receive(connection, server=False)
        response = self.handle_response(stream)
        return response

    def handle_response(self, stream):
        response = beretta.decode(next(stream))
        rtype = response[0]
        if rtype == ":reply":
            return response[1]
        elif rtype == ":noreply":
            return None
        elif rtype == ":error":
            raise ValueError(response)
        else:
            raise NotImplementedError

    def call(self, function, args, **kwargs):
        return self.request(":call", function, args, kwargs)

    def cast(self, function, args, **kwargs):
        return self.request(":cast", function, args, kwargs)
