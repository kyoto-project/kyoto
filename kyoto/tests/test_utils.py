import unittest

import beretta
import kyoto.utils.berp
import kyoto.utils.modules
import kyoto.utils.validation


class BERPTestCase(unittest.TestCase):

    def setUp(self):
        self.request = beretta.encode((":call", ":dummy", ":echo", ["hello"]))

    def test_pack_message(self):
        message = kyoto.utils.berp.pack(self.request)
        self.assertEqual(len(message), 4 + len(self.request))

    def test_unpack_message(self):
        message = kyoto.utils.berp.pack(self.request)
        length, body, tail = kyoto.utils.berp.unpack(message)
        self.assertEqual(length, len(self.request))
        self.assertEqual(body, self.request)
        self.assertEqual(tail, b"")

    def test_unpack_message_with_incomplete_head(self):
        message = kyoto.utils.berp.pack(self.request)[:2]
        with self.assertRaises(ValueError, message="Incomplete BERP head: received 2 of 4 bytes"):
            length, body, tail = kyoto.utils.berp.unpack(message)

    def test_unpack_message_with_incomplete_body(self):
        message = kyoto.utils.berp.pack(self.request)[:-1]
        with self.assertRaises(ValueError, message="Incomplete BERP body: received 40 of 41 bytes"):
            length, body, tail = kyoto.utils.berp.unpack(message)

    # TODO:
    # def test_unpack_message_with_invalid_header(self):
    #     message = kyoto.utils.berp.pack(self.request)[1:]
    #     length, body, tail = kyoto.utils.berp.unpack(message)


class ValidationTestCase(unittest.TestCase):

    def test_not_tuple(self):
        self.assertFalse(kyoto.utils.validation.is_valid_request([":call", ":Module", ":function", []]))

    def test_info_incomplete(self):
        self.assertFalse(kyoto.utils.validation.is_valid_info((":info", ":stream")))

    def test_info_invalid_type(self):
        self.assertFalse(kyoto.utils.validation.is_valid_info((":info", ":magic", [])))

    def test_info_args_not_list(self):
        self.assertFalse(kyoto.utils.validation.is_valid_info((":info", ":stream", (1, 2))))

    def test_info_valid(self):
        self.assertTrue(kyoto.utils.validation.is_valid_info((":info", ":callback", [])))
        self.assertTrue(kyoto.utils.validation.is_valid_info((":info", ":stream", [])))
        self.assertTrue(kyoto.utils.validation.is_valid_info((":info", ":cache", [])))

    def test_err_incomplete(self):
        self.assertFalse(kyoto.utils.validation.is_valid_error_response((":error",)))
        self.assertFalse(kyoto.utils.validation.is_valid_error_response((":error", (":server", ))))
        self.assertFalse(kyoto.utils.validation.is_valid_error_response((":error", (":server", 2))))
        self.assertFalse(kyoto.utils.validation.is_valid_error_response((":error", (":server", 2, "NameError"))))
        self.assertFalse(kyoto.utils.validation.is_valid_error_response((":error", (":server", 2, "NameError", "Message"))))

    def test_err_valid(self):
        self.assertTrue(kyoto.utils.validation.is_valid_error_response((":error", (":server", 2, "NameError", "No such function", []))))
        self.assertTrue(kyoto.utils.validation.is_valid_error_response((":error", (":user", 500, "ValueError", "with user message", []))))

class ModulesTestCase(unittest.TestCase):

    def test_get_module_functions(self):
        functions = kyoto.utils.modules.get_module_functions(kyoto.utils.modules, False)
        self.assertTrue(len(functions) > 0)
        self.assertTrue(isinstance(functions, dict))
        self.assertIn("get_module_functions", functions)

    def test_get_module_functions_as_strings(self):
        functions = kyoto.utils.modules.get_module_functions(kyoto.utils.modules, True)
        self.assertTrue(len(functions) > 0)
        self.assertTrue(isinstance(functions, tuple))
        self.assertIn("get_module_functions", functions)

    def test_get_module_name(self):
        name = kyoto.utils.modules.get_module_name(kyoto.utils.modules)
        self.assertEqual(name, "modules")
