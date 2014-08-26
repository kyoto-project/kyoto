import unittest
import kyoto
import kyoto.tests.dummy


class ModuleTestCase(unittest.TestCase):

    def setUp(self):
        self.module = kyoto.tests.dummy

    def test_call_public_method(self):
        response = self.module.echo("hello")
        self.assertEqual(response, "hello?")

    def test_call_private_method(self):
        response = self.module.private_echo("hello")
        self.assertEqual(response, "hello!")
