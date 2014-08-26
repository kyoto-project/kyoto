import struct
import beretta
import unittest
import gevent.queue
import gevent.socket

import kyoto.conf
import kyoto.server
import kyoto.utils.berp
import kyoto.tests.dummy
import kyoto.network.stream


class AgentTestCase(unittest.TestCase):

    def setUp(self):
        self.modules = [
            kyoto.tests.dummy,
        ]
        self.agent = kyoto.server.Agent(self.modules, ('localhost', 1337))

    def test_unknown_module(self):
        response = self.agent.handle(beretta.encode((":call", ":Kittens", ":echo", ["hello"])))
        self.assertEqual(beretta.decode(next(response)), (':error', (':server', 1, 'NameError', "No such module: ':Kittens'", [])))

    def test_unknown_function(self):
        response = self.agent.handle(beretta.encode((":call", ":dummy", ":kittens", ["hello"])))
        self.assertEqual(beretta.decode(next(response)), (':error', (':server', 2, 'NameError', "No such function: ':kittens'", [])))

    def test_invalid_mfa(self):
        response = self.agent.handle(beretta.encode((":call", ":dummy", ":kittens")))
        response = beretta.decode(next(response))
        self.assertEqual(response[1][0], ":server")
        self.assertEqual(response[1][1], 4)
        self.assertEqual(response[1][2], "ValueError")
        self.assertTrue(response[1][3].startswith("Invalid MFA"))

    def test_sync_request(self):
        message = beretta.encode((":call", ":dummy", ":echo", ["hello"]))
        response = self.agent.handle(message)
        self.assertEqual(next(response), beretta.encode((":reply", "hello?")))

    def test_async_request(self):
        message = beretta.encode((":cast", ":dummy", ":echo", ["hello"]))
        response = self.agent.handle(message)
        self.assertEqual(next(response), beretta.encode((":noreply",)))

    def test_sync_with_streaming_request(self):
        self.assertEqual(self.agent.state['stream']['on'], False)
        self.assertEqual(self.agent.state['stream']['request'], None)
        info = beretta.encode((":info", ":stream", []))
        request = beretta.encode((":call", ":dummy", ":streaming_echo_request", []))
        with self.assertRaises(StopIteration):
            response = next(self.agent.handle(info))
        self.assertEqual(self.agent.state['stream']['on'], True)
        self.assertEqual(self.agent.state['stream']['request'], None)
        with self.assertRaises(StopIteration):
            response = next(self.agent.handle(request))
        self.assertEqual(self.agent.state['stream']['on'], True)
        self.assertEqual(self.agent.state['stream']['request'], (":call", ":dummy", ":streaming_echo_request", []))
        for message in ["hello" for _ in range(10)]:
            with self.assertRaises(StopIteration):
                response = next(self.agent.handle(message))
        response = self.agent.handle(b"")
        self.assertEqual(beretta.decode(next(response)), (":info", ":stream", []))
        self.assertEqual(beretta.decode(next(response)), (":noreply", ))
        for _ in range(10):
            self.assertEqual(next(response), "hello")
        self.assertEqual(next(response), b"")
        self.assertEqual(self.agent.state['stream']['on'], False)
        self.assertEqual(self.agent.state['stream']['request'], None)

    def test_sync_call_with_streaming_response(self):
        request = beretta.encode((":call", ":dummy", ":streaming_echo_response", ["hello"]))
        response = self.agent.handle(request)
        self.assertEqual(beretta.decode(next(response)), (":info", ":stream", []))
        self.assertEqual(beretta.decode(next(response)), (":reply", {"count": 10}))
        for _ in range(10):
            self.assertEqual(next(response), "hello?")
        self.assertEqual(next(response), b"")

    def test_sync_call_with_broken_streaming_echo(self):
        request = beretta.encode((":call", ":dummy", ":broken_streaming_echo", ["hello"]))
        response = self.agent.handle(request)
        self.assertEqual(beretta.decode(next(response)), (":info", ":stream", []))
        self.assertEqual(beretta.decode(next(response)), (":reply", {"count": 10}))
        self.assertEqual(next(response), b"")

    def test_async_call_with_streaming_response(self):
        request = beretta.encode((":cast", ":dummy", ":streaming_echo_response", ["hello"]))
        response = self.agent.handle(request)
        self.assertEqual(beretta.decode(next(response)), (':noreply',))

    def test_sync_call_exception(self):
        request = beretta.encode((":call", ":dummy", ":echo_with_exception", ["hello"]))
        response = beretta.decode(next(self.agent.handle(request)))
        self.assertEqual(response[0], ":error")
        self.assertEqual(response[1][0], ":user")
        self.assertEqual(response[1][2], "ValueError")
        self.assertEqual(response[1][3], "This is exception with your text: hello")
        self.assertEqual(response[1][4][0], "Traceback (most recent call last):")

    def test_async_call_exception(self):
        request = beretta.encode(
            (":cast", ":dummy", ":echo_with_exception", ["hello"]))
        response = self.agent.handle(request)
        self.assertEqual(beretta.decode(next(response)), (":noreply", ))

    def test_call_with_malformed_request(self):
        request = beretta.encode((":call", ":dummy", ":echo", ["hello"]))[2:]
        response = next(self.agent.handle(request))
        self.assertEqual(beretta.decode(response), (":error", (":server", 3, "ValueError", "Corrupt request data", [])))

    def test_stream_call_with_malformed_request(self):
        self.assertEqual(self.agent.state['stream']['on'], False)
        self.assertEqual(self.agent.state['stream']['request'], None)
        info = beretta.encode((":info", ":stream", []))
        request = beretta.encode((":call", ":dummy", ":echo", ["hello"]))[2:]
        with self.assertRaises(StopIteration):
            response = next(self.agent.handle(info))
        response = next(self.agent.handle(request))
        self.assertEqual(beretta.decode(response), (":error", (":server", 3, "ValueError", "Corrupt request data", [])))
        self.assertEqual(self.agent.state['stream']['on'], False)
        self.assertEqual(self.agent.state['stream']['request'], None)


class ServerTestCase(unittest.TestCase):

    def setUp(self):
        self.address = ('localhost', 1337)
        self.server = kyoto.server.BertRPCServer([kyoto.tests.dummy])
        self.server.start()
        self.connection = gevent.socket.create_connection(self.address)

    def test_unknown_module(self):
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":Kittens", ":echo", ["hello"])))
        status = self.connection.sendall(message)
        response = kyoto.network.stream.receive(self.connection)
        self.assertEqual(beretta.decode(next(response)), (':error', (':server', 1, 'NameError', "No such module: ':Kittens'", [])))

    def test_unknown_function(self):
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":kittens", ["hello"])))
        status = self.connection.sendall(message)
        response = kyoto.network.stream.receive(self.connection)
        self.assertEqual(beretta.decode(next(response)), (':error', (':server', 2, 'NameError', "No such function: ':kittens'", [])))

    def test_sync_request(self):
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":echo", ["hello"])))
        status = self.connection.sendall(message)
        response = kyoto.network.stream.receive(self.connection)
        self.assertEqual(beretta.decode(next(response)), (":reply", "hello?"))

    def test_async_request(self):
        message = kyoto.utils.berp.pack(beretta.encode((":cast", ":dummy", ":echo", ["hello"])))
        status = self.connection.sendall(message)
        response = kyoto.network.stream.receive(self.connection)
        self.assertEqual(beretta.decode(next(response)), (":noreply", ))

    def test_sync_with_streaming_request(self):
        message = kyoto.utils.berp.pack(beretta.encode((":info", ":stream", [])))
        status = self.connection.sendall(message)
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":streaming_echo_request", [])))
        status = self.connection.sendall(message)
        for message in [b"hello" for _ in range(10)]:
            status = self.connection.sendall(kyoto.utils.berp.pack(message))
        status = self.connection.sendall(kyoto.utils.berp.pack(b""))
        response = kyoto.network.stream.receive(self.connection)
        self.assertEqual(
            beretta.decode(next(response)), (":info", ":stream", []))
        self.assertEqual(beretta.decode(next(response)), (":noreply", ))
        for _ in range(10):
            self.assertEqual(next(response), b"hello")
        self.assertEqual(next(response), b"")

    def test_sync_call_with_streaming_response(self):
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":streaming_echo_response", ["hello"])))
        status = self.connection.sendall(message)
        response = kyoto.network.stream.receive(self.connection)
        self.assertEqual(
            beretta.decode(next(response)), (":info", ":stream", []))
        self.assertEqual(
            beretta.decode(next(response)), (":reply", {"count": 10}))
        for _ in range(10):
            self.assertEqual(next(response), b"hello?")
        self.assertEqual(next(response), b"")

    def test_sync_call_with_broken_streaming_echo(self):
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":broken_streaming_echo", ["hello"])))
        status = self.connection.sendall(message)
        response = kyoto.network.stream.receive(self.connection)
        self.assertEqual(
            beretta.decode(next(response)), (":info", ":stream", []))
        self.assertEqual(
            beretta.decode(next(response)), (":reply", {"count": 10}))
        self.assertEqual(next(response), b"")

    def test_async_call_with_streaming_response(self):
        message = kyoto.utils.berp.pack(beretta.encode((":cast", ":dummy", ":streaming_echo_response", ["hello"])))
        status = self.connection.sendall(message)
        response = kyoto.network.stream.receive(self.connection)
        self.assertEqual(beretta.decode(next(response)), (':noreply',))

    def test_sync_call_exception(self):
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":echo_with_exception", ["hello"])))
        status = self.connection.sendall(message)
        response = beretta.decode(
            next(kyoto.network.stream.receive(self.connection)))
        self.assertEqual(response[0], ":error")
        self.assertEqual(response[1][0], ":user")
        self.assertEqual(response[1][2], "ValueError")
        self.assertEqual(
            response[1][3], "This is exception with your text: hello")
        self.assertEqual(
            response[1][4][0], "Traceback (most recent call last):")

    def test_async_call_exception(self):
        message = kyoto.utils.berp.pack(beretta.encode((":cast", ":dummy", ":echo_with_exception", ["hello"])))
        status = self.connection.sendall(message)
        response = kyoto.network.stream.receive(self.connection)
        self.assertEqual(beretta.decode(next(response)), (":noreply", ))

    def test_call_with_malformed_request(self):
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":echo", ["hello"]))[2:])
        status = self.connection.sendall(message)
        response = kyoto.network.stream.receive(self.connection)
        self.assertEqual(beretta.decode(next(response)), (":error", (":server", 3, "ValueError", "Corrupt request data", [])))

    def test_stream_call_with_malformed_request(self):
        message = kyoto.utils.berp.pack(beretta.encode((":info", ":stream", [])))
        status = self.connection.sendall(message)
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":echo", ["hello"]))[2:])
        status = self.connection.sendall(message)
        response = kyoto.network.stream.receive(self.connection)
        self.assertEqual(beretta.decode(next(response)), (":error", (":server", 3, "ValueError", "Corrupt request data", [])))

    def test_large_berp(self):
        packet_size = kyoto.conf.settings.MAX_BERP_SIZE + 1024
        message = struct.pack('>I', packet_size) + b"message"
        status = self.connection.sendall(message)
        response = kyoto.network.stream.receive(self.connection)
        self.assertEqual(beretta.decode(next(response)), (':error', (':protocol', 3, 'MaxBERPSizeError', 'Invalid BERP length: 33554432/33555456', [])))

    def tearDown(self):
        self.connection.close()
        self.server.stop()
