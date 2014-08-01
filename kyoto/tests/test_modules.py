import unittest
import kyoto
import kyoto.tests.dummy


class ModuleTestCase(unittest.TestCase):

    def setUp(self):
        self.module = kyoto.tests.dummy.Echo()

    def test_call_public_method(self):
        response = self.module.echo("hello")
        self.assertEqual(response, "hello?")

    def test_call_private_method(self):
        response = self.module.private_echo("hello")
        self.assertEqual(response, "hello!")

    def test_get_public_methods_as_dict(self):
        methods = self.module.methods(as_strings=False)
        self.assertTrue(isinstance(methods, dict), True)
        self.assertIn("echo", methods.keys())

    def test_call_public_method_from_dict(self):
        methods = self.module.methods(as_strings=False)
        response = methods["echo"]("hello")
        self.assertEqual(response, "hello?")

    def test_get_public_methods_as_strings(self):
        methods = self.module.methods(as_strings=True)
        self.assertIn("echo", methods)

    def test_get_private_methods_as_dict(self):
        methods = self.module.methods(as_strings=False)
        self.assertTrue(isinstance(methods, dict), True)
        self.assertNotIn("private_echo", methods.keys())

    def test_call_private_method_from_dict(self):
        methods = self.module.methods(as_strings=False)
        with self.assertRaises(KeyError):
            response = methods["private_echo"]("hello")
            self.assertEqual(response, "hello!")

    def test_get_private_methods_as_strings(self):
        methods = self.module.methods(as_strings=True)
        is_method_exists = hasattr(self.module, "private_echo")
        self.assertEqual(is_method_exists, True)
        self.assertNotIn("private_echo", methods)
