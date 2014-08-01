import kyoto
import gevent


class Echo(kyoto.Module):

  def echo(self, message):
    """
    Standard client-server example
    """
    return u"{0}?".format(message)

  @kyoto.private
  def private_echo(self, message):
    """
    Same as above, but can't be used outside of this module
    """
    return u"{0}!".format(message)

  def blocking_echo(self, message):
    gevent.sleep(100)
    return u"{0}?".format(message)

  def true_blocking_echo(self, message):
    import time
    time.sleep(100)
    return u"{0}?".format(message)

  def streaming_echo_request(self, stream):
    yield None
    for message in stream:
      yield message

  def streaming_echo_response(self, message):
    yield {
      'count': 10,
    }
    for x in range(10):
      yield u"{0}?".format(message)

  def broken_streaming_echo(self, message):
    """
    Must act like other streaming echo examples, but actually don't returns byte stream
    """
    yield {
      'count': 10,
    }

  def echo_with_exception(self, message):
    message = "This is exception with your text: {0}".format(message)
    raise ValueError(message)

  def streaming_echo_length(self, stream):
    length = 0
    for message in stream:
      length += len(message)
    return length
