import kyoto
import kyoto.conf

import gevent
import threading

def echo(message):
    """
    Standard client-server example
    """
    return u"{0}?".format(message)

@kyoto.private
def private_echo(message):
    """
    Same as above, but can't be used outside of this module
    """
    return u"{0}!".format(message)

def blocking_echo(message):
    gevent.sleep(100)
    return u"{0}?".format(message)

def true_blocking_echo(message):
    import time
    time.sleep(100)
    return u"{0}?".format(message)

def streaming_echo_request(stream):
    yield None
    for message in stream:
        yield message

def streaming_echo_response(message):
    yield {
        'count': 10,
    }
    for x in range(10):
        yield u"{0}?".format(message)

def broken_streaming_echo(message):
    """
    Must act like other streaming echo examples, but actually don't returns byte stream
    """
    yield {
        'count': 10,
    }

def echo_with_exception(message):
    message = "This is exception with your text: {0}".format(message)
    raise ValueError(message)

def streaming_echo_length(stream):
    length = 0
    for message in stream:
        length += len(message)
    return length

def large_echo(message):
    """
    Raises MAX_BERP_SIZE exception
    """
    message = message * kyoto.conf.settings.MAX_BERP_SIZE
    return message

@kyoto.blocking
def blocking_echo():
    """
    Must be executed in dedicated thread
    """
    thread = threading.current_thread()
    return thread.ident
