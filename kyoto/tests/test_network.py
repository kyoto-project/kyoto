import beretta
import unittest
import gevent.socket

import kyoto.server
import kyoto.tests.dummy
import kyoto.utils.berp
import kyoto.network.stream
import kyoto.network.connection


class SingleConnectionManagerTestCase(unittest.TestCase):

    def setUp(self):
        self.address = ('localhost', 1337)
        self.server = kyoto.server.BertRPCServer([kyoto.tests.dummy])
        self.server.start()
        self.connections = kyoto.network.connection.SingleConnectionManager(self.address, 5)

    def test_get_connection(self):
        connection = self.connections.acquire()
        self.assertTrue(isinstance(connection, gevent.socket.socket))

    def test_use_connection(self):
        connection = self.connections.acquire()
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":echo", ["hello"])))
        connection.sendall(message)
        response = kyoto.network.stream.receive(connection)
        self.assertEqual(beretta.decode(next(response)), (":reply", "hello?"))
        self.connections.release(connection)

    def test_release_connection(self):
        connection = self.connections.acquire()
        self.assertFalse(connection.closed)
        self.connections.release(connection)
        self.assertTrue(connection.closed)

    def tearDown(self):
        self.server.stop()
        self.connections.clear()


class SharedConnectionManagerTestCase(unittest.TestCase):

    def setUp(self):
        self.address = ('localhost', 1337)
        self.server = kyoto.server.BertRPCServer([kyoto.tests.dummy])
        self.server.start()
        self.connections = kyoto.network.connection.SharedConnectionManager(self.address, 5)

    def test_get_connection(self):
        self.assertFalse(self.connections.semaphore.locked())
        connection = self.connections.acquire()
        self.assertTrue(isinstance(connection, gevent.socket.socket))
        self.assertTrue(self.connections.semaphore.locked())
        self.connections.semaphore.release()
        self.assertFalse(self.connections.semaphore.locked())

    def test_use_connection(self):
        connection = self.connections.acquire()
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":echo", ["hello"])))
        connection.sendall(message)
        response = kyoto.network.stream.receive(connection)
        self.assertEqual(beretta.decode(next(response)), (":reply", "hello?"))
        self.connections.release(connection)

    def test_reopen_connection(self):
        connection = self.connections.acquire()
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":echo", ["hello"])))
        connection.sendall(message)
        response = kyoto.network.stream.receive(connection)
        self.assertEqual(beretta.decode(next(response)), (":reply", "hello?"))
        self.connections.release(connection)
        connection.close()
        self.assertTrue(connection.closed)
        connection = self.connections.acquire()
        self.assertFalse(connection.closed)
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":echo", ["hello"])))
        connection.sendall(message)
        response = kyoto.network.stream.receive(connection)
        self.assertEqual(beretta.decode(next(response)), (":reply", "hello?"))
        self.connections.release(connection)

    def test_release_connection(self):
        self.assertFalse(self.connections.semaphore.locked())
        connection = self.connections.acquire()
        self.assertTrue(self.connections.semaphore.locked())
        self.assertFalse(connection.closed)
        self.connections.release(connection)
        self.assertFalse(connection.closed)
        self.assertFalse(self.connections.semaphore.locked())

    def tearDown(self):
        self.server.stop()
        self.connections.clear()

class StreamTestCase(unittest.TestCase):

    def setUp(self):
        self.address = ('localhost', 1337)
        self.server = kyoto.server.BertRPCServer([kyoto.tests.dummy])
        self.server.start()
        self.connection = gevent.socket.create_connection(self.address)

    def test_receive_stream(self):
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":echo", ["hello"])))
        self.connection.sendall(message)
        response = kyoto.network.stream.receive(self.connection)
        self.assertEqual(beretta.decode(next(response)), (":reply", "hello?"))

    def test_receive_large_stream(self):
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":large_echo", ["hello"])))
        self.connection.sendall(message)
        response = kyoto.network.stream.receive(self.connection)
        with self.assertRaises(kyoto.utils.berp.MaxBERPSizeError):
            message = next(response)

    def test_send_file_stream(self):
        info = kyoto.utils.berp.pack(beretta.encode((":info", ":stream", [])))
        self.connection.sendall(info)
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":streaming_echo_length", [])))
        self.connection.sendall(message)
        with open("/etc/passwd", "rb") as source:
            stream = kyoto.network.stream.send(source)
            for chunk in stream:
                self.connection.sendall(chunk)
        response = kyoto.network.stream.receive(self.connection)
        reply, length = beretta.decode(next(response))
        self.assertTrue(length > 0)

    def test_send_generator_stream(self):
        def payload(message):
            for x in range(10):
                yield message
        info = kyoto.utils.berp.pack(beretta.encode((":info", ":stream", [])))
        self.connection.sendall(info)
        message = kyoto.utils.berp.pack(beretta.encode((":call", ":dummy", ":streaming_echo_length", [])))
        self.connection.sendall(message)
        stream = kyoto.network.stream.send(payload("hello"))
        for chunk in stream:
            self.connection.sendall(chunk)
        response = kyoto.network.stream.receive(self.connection)
        reply, length = beretta.decode(next(response))
        self.assertEqual(length, 50)

    def test_send_unsupported_type_stream(self):
        with self.assertRaises(ValueError):
            stream = next(kyoto.network.stream.send(b"hello"))

    def tearDown(self):
        self.connection.close()
        self.server.stop()
