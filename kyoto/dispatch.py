import types
import gevent
import traceback
import termformat

import kyoto
import kyoto.conf
import kyoto.utils.modules
import kyoto.utils.validation

try:
    # Python 2.x
    from itertools import izip
except ImportError:
    # Python 3.x
    izip = zip


class Dispatcher(object):

    __slots__ = ("address", "handlers", "modules")

    def __init__(self, modules, address):
        self.address = address
        self.handlers = {
            ":call": self.handle_call,
            ":cast": self.handle_cast,
        }
        self.modules = self.transform_modules(modules)

    def transform_modules(self, modules):
        """
        Creates dispatching dictionary from given list of modules:
        [kyoto.tests.dummy] => {
          ":dummy": <module 'kyoto.tests.dummy' object>,
        }
        """
        def transform(module):
            name = kyoto.utils.modules.get_module_name(module)
            return (termformat.binary_to_atom(name), module)
        return dict((transform(m) for m in modules))

    def transform_exceptions(function):
        """
        Catches exceptions and transforms it to BERT response terms.
        Python: raise ValueError("with message")
        BERT: {error, {user, 500, "ValueError", "with message", ["Traceback (most recent call last):", ...]}}
        """
        def transform(*args, **kwargs):
            try:
                response = function(*args, **kwargs)
            except Exception as exception:
                name = exception.__class__.__name__
                message = str(exception)
                trace = traceback.format_exc().splitlines()
                return (":error", (":user", 500, name, message, trace))
            else:
                return response
        return transform

    def transform_response(function):
        """
        Transforms function output to BERT response terms.
        1. No response
            Python: None
            BERT: {noreply}
        2. Has response
            Python: {
                      "length": 1024,
                      "checksum": "06aef8bb71e72b2abec01d4bd3aa9dda48fd20e6",
                    }
            BERT: {reply, {
                      "length": 1024,
                      "checksum": "06aef8bb71e72b2abec01d4bd3aa9dda48fd20e6",
                  }}
        3. Streaming response
            Python: {"content-type": "image/png"}
                    {        binary data        }
                    {        binary data        }
            BERT: {info, stream, []}
                  {reply, {"content-type": "image/png"}}
                  {             binary data            }
                  {             binary data            }
        """
        def transform(*args, **kwargs):
            response = function(*args, **kwargs)
            if response:
                if isinstance(response, types.GeneratorType):
                    yield (":info", ":stream", [])
                    message = next(response)
                    if message:
                        yield (":reply", message)
                    else:
                        yield (":noreply",)
                    for message in response:
                        yield message
                else:
                    if kyoto.utils.validation.is_valid_error_response(response):
                        yield response
                    else:
                        yield (":reply", response)
            else:
                yield (":noreply",)
        return transform

    @transform_response
    def handle(self, request, **kwargs):
        rtype, module, function, args = request
        if module in self.modules:
            module = self.modules.get(module)
            name = termformat.atom_to_binary(function)
            function = getattr(module, name, None)
            if function and kyoto.utils.modules.is_callable_object(function):
                if kyoto.is_blocking(function):
                    future = kyoto.conf.settings.BLOCKING_POOL.submit(self.handle_call, function, args, **kwargs)
                    if rtype == ":call":
                        response = future.result()
                    else:
                        response = None
                else:
                    response = self.handlers[rtype](function, args, **kwargs)
                return response
            else:
                function = termformat.binary_to_atom(name)
                return (":error", (":server", 2, "NameError", "No such function: '{0}'".format(function), []))
        else:
            return (":error", (":server", 1, "NameError", "No such module: '{0}'".format(module), []))

    @transform_exceptions
    def handle_call(self, function, args, **kwargs):
        return function(*args, **kwargs)

    @transform_exceptions
    def handle_cast(self, function, args, **kwargs):
        gevent.spawn(function, *args, **kwargs)
