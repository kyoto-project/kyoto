import logging
import beretta

import gevent
import gevent.queue
import gevent.socket
import gevent.server

import kyoto.conf
import kyoto.dispatch
import kyoto.utils.berp
import kyoto.utils.validation
import kyoto.network.stream


class Agent(object):

    __slots__ = ("state", "address", "logger", "dispatcher")

    def __init__(self, modules, address):
        self.state = {
            'stream': {
                'on': False,
                'request': None,
            },
        }
        self.address = address
        self.logger = logging.getLogger("kyoto.server.Agent")
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

    def __init__(self, modules):
        self.modules = modules
        self.address = kyoto.conf.settings.BIND_ADDRESS
        self.logger = logging.getLogger('kyoto.server.BertRPCServer')
        super(BertRPCServer, self).__init__(self.address)

    def handle(self, connection, address):
        self.logger.info("{0}:{1} connected".format(*address))
        agent = Agent(self.modules, address)
        stream = kyoto.network.stream.receive(connection)
        try:
            for request in stream:
                for response in agent.handle(request):
                    message = kyoto.utils.berp.pack(response)
                    connection.sendall(message)
        except Exception as exception:
            self.logger.exception(exception)
        finally:
            connection.close()
        self.logger.info("{0}:{1} disconnected".format(*address))
