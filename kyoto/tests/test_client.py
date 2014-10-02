import unittest
import kyoto.server
import kyoto.tests.dummy
import kyoto.client


class ServiceTestCase(unittest.TestCase):

    def setUp(self):
        self.address = ('localhost', 1337)
        self.server = kyoto.server.BertRPCServer([kyoto.tests.dummy])
        self.server.start()
        self.service = kyoto.client.Service(self.address, ":dummy")

    def test_invalid_module_name_type(self):
        with self.assertRaises(ValueError):
            service = kyoto.client.Service(self.address, "dummy")
        service = kyoto.client.Service(self.address, ":dummy")

    def test_sync_request(self):
        response = self.service.call(":echo", ["hello"])
        self.assertEqual(response, "hello?")

    def test_async_request(self):
        response = self.service.cast(":echo", ["hello"])
        self.assertEqual(response, None)

    def tearDown(self):
        self.server.stop()
