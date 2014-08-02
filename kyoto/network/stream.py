import io
import types
import beretta

import kyoto.conf
import kyoto.utils.berp

try:
    # Python 2.x
    file = file
except NameError:
    # Python 3.x
    file = io.IOBase


def send(source):
    if isinstance(source, file):
        while source:
            chunk = source.read(kyoto.conf.settings.READ_CHUNK_SIZE)
            if not chunk:
                break
            yield kyoto.utils.berp.pack(chunk)
    elif isinstance(source, types.GeneratorType):
        for chunk in source:
            yield kyoto.utils.berp.pack(chunk)
    else:
        raise ValueError("Stream must be file-like or generator object")
    yield b"\x00\x00\x00\x00"


def receive(connection, server=True):
    buffer = b""
    while connection:
        message = connection.recv(kyoto.conf.settings.READ_CHUNK_SIZE)
        if message:
            buffer += message
            while len(buffer) >= 4:
                try:
                    length, message, tail = kyoto.utils.berp.unpack(buffer)
                except ValueError as exception:
                    break  # received incomplete packet, continue loop
                except kyoto.utils.berp.MaxBERPLengthError as exception:
                    if server:
                        exception = (":error", (":protocol", 3, "MaxBERPLengthError", str(exception), []))
                        exception = kyoto.utils.berp.pack(beretta.encode(exception))
                        connection.sendall(exception)
                    raise
                else:
                    buffer = tail
                    yield message
        else:
            break
