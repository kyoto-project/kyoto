import time
import unittest
import gevent.queue

import kyoto
import kyoto.dispatch
import kyoto.tests.dummy


class DispatcherTestCase(unittest.TestCase):

  def setUp(self):
    self.modules = [
      kyoto.tests.dummy.Echo,
    ]
    self.address = ("localhost", 1337)
    self.dispatcher = kyoto.dispatch.Dispatcher(self.modules, self.address)

  def test_registered_modules(self):
    self.assertIn(":Echo", self.dispatcher.modules)
    self.assertTrue(len(self.dispatcher.modules[":Echo"]) > 0)

  def test_unknown_module(self):
    response = self.dispatcher.handle((":call", ":Kittens", ":echo", ["hello"]))
    self.assertEqual(next(response), (':error', (':server', 1, 'NameError', "No such module: ':Kittens'", [])))

  def test_unknown_function(self):
    response = self.dispatcher.handle((":call", ":Echo", ":kittens", ["hello"]))
    self.assertEqual(next(response), (':error', (':server', 2, 'NameError', "No such function: ':kittens'", [])))

  def test_sync_call(self):
    response = self.dispatcher.handle((":call", ":Echo", ":echo", ["hello"]))
    self.assertEqual(next(response), (":reply", "hello?"))

  def test_async_call(self):
    response = self.dispatcher.handle((":cast", ":Echo", ":blocking_echo", ["hello"]))
    start = time.time()
    self.assertEqual(next(response), (":noreply", ))
    finish = time.time()
    self.assertTrue(finish - start < 100.0)

  def test_sync_call_with_streaming_request(self):
    request = (":call", ":Echo", ":streaming_echo_request", [])
    response = self.dispatcher.handle(request, stream=["hello" for _ in range(10)])
    self.assertEqual(next(response), (":info", ":stream", []))
    self.assertEqual(next(response), (":noreply", ))
    for x in range(10):
      self.assertEqual(next(response), "hello")
    with self.assertRaises(StopIteration):
      self.assertEqual(next(response), "hello")

  def test_sync_call_with_streaming_response(self):
    request = (":call", ":Echo", ":streaming_echo_response", ["hello"])
    response = self.dispatcher.handle(request)
    self.assertEqual(next(response), (":info", ":stream", []))
    self.assertEqual(next(response), (":reply", {"count": 10}))
    self.assertEqual(next(response), "hello?")

  def test_async_call_with_streaming_response(self):
    request = (":cast", ":Echo", ":streaming_echo_response", ["hello"])
    response = self.dispatcher.handle(request)
    self.assertEqual(next(response), (':noreply',))

  def test_sync_call_broken_streaming_echo(self):
    request = (":call", ":Echo", ":broken_streaming_echo", ["hello"])
    response = self.dispatcher.handle(request)
    self.assertEqual(next(response), (":info", ":stream", []))
    self.assertEqual(next(response), (":reply", {"count": 10}))
    with self.assertRaises(StopIteration):
      self.assertEqual(next(response), "hello?")

  def test_sync_call_exception(self):
    request = (":call", ":Echo", ":echo_with_exception", ["hello"])
    response = next(self.dispatcher.handle(request))
    self.assertEqual(response[0], ":error")
    self.assertEqual(response[1][0], ":user")
    self.assertEqual(response[1][2], "ValueError")
    self.assertEqual(response[1][3], "This is exception with your text: hello")
    self.assertEqual(response[1][4][0], "Traceback (most recent call last):")

  def test_async_call_exception(self):
    request = (":cast", ":Echo", ":echo_with_exception", ["hello"])
    response = self.dispatcher.handle(request)
    self.assertEqual(next(response), (":noreply", ))
