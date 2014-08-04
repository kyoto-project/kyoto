import gevent
import gevent.queue
import gevent.socket
import gevent.server

import beretta
import kyoto.conf
import kyoto.dispatch
import kyoto.utils.berp
import kyoto.utils.validation
import kyoto.network.stream


class Agent(object):

    def __init__(self, modules, address):
        self.state = {
            'stream': {
                'on': False,
                'request': None,
            },
        }
        self.address = address
        self.dispatcher = kyoto.dispatch.Dispatcher(modules, address)

    def transform_response(function):
        def transform(*args, **kwargs):
            response = function(*args, **kwargs)
            try:
                message = next(response)
            except StopIteration:
                pass
            else:
                yield beretta.encode(message)
                if message == (":info", ":stream", []):
                    yield beretta.encode(next(response))
                    for message in response:
                        yield message
                    yield b""
        return transform

    @transform_response
    def handle(self, message):
        if not self.state['stream']['on']:
            try:
                request = beretta.decode(message)
            except ValueError:
                yield (":error", (":server", 3, "ValueError", "Corrupt request data", []))
            else:
                if kyoto.utils.validation.is_valid_request(request):
                    for message in self.dispatcher.handle(request):
                        yield message
                elif kyoto.utils.validation.is_valid_info(request):
                    if request[1] == ":stream":
                        self.state['stream']['on'] = True
                        self.state['stream']['queue'] = gevent.queue.Queue()
                else:
                    yield (":error", (":server", 4, "ValueError", "Invalid MFA: {0}".format(request), []))
        else:
            if not self.state['stream']['request']:
                try:
                    request = beretta.decode(message)
                except ValueError:
                    self.state['stream']['on'] = False
                    yield (":error", (":server", 3, "ValueError", "Corrupt request data", []))
                else:
                    if kyoto.utils.validation.is_valid_request(request):
                        self.state['stream']['request'] = request
                        self.state['stream']['worker'] = gevent.spawn(self.dispatcher.handle,
                                                                      self.state['stream']['request'],
                                                                      stream=self.state['stream']['queue'])
                    else:
                        raise NotImplementedError
            else:
                if message:
                    self.state['stream']['queue'].put(message)
                else:
                    self.state['stream']['on'] = False
                    self.state['stream']['request'] = None
                    self.state['stream']['queue'].put(StopIteration)
                    response = self.state['stream']['worker'].get()
                    for message in response:
                        yield message


class BertRPCServer(gevent.server.StreamServer):

    def __init__(self, modules, *args, **kwargs):
        self.modules = modules
        self.address = kyoto.conf.settings.BIND_ADDRESS
        super(BertRPCServer, self).__init__(self.address, *args, **kwargs)

    def handle(self, connection, address):
        agent = Agent(self.modules, address)
        stream = kyoto.network.stream.receive(connection)
        try:
            for request in stream:
                for response in agent.handle(request):
                    message = kyoto.utils.berp.pack(response)
                    connection.sendall(message)
        finally:
            connection.close()
