import struct
import kyoto.conf


class MaxBERPSizeError(Exception):
    pass


def pack(message):
    if not isinstance(message, bytes):
        message = message.encode("utf-8")
    return struct.pack(">I", len(message)) + message


def unpack(message):
    head, tail = message[:4], message[4:]
    if len(head) == 4:
        length, = struct.unpack(">I", head)
    else:
        message = "Incomplete BERP head: received {0} of 4 bytes"
        raise ValueError(message.format(len(head)))
    if length > kyoto.conf.settings.MAX_BERP_SIZE:
        message = "Invalid BERP length: {0}/{1}"
        raise MaxBERPSizeError(
            message.format(kyoto.conf.settings.MAX_BERP_SIZE, length)
        )
    body, tail = tail[:length], tail[length:]
    if len(body) < length:
        message = "Incomplete BERP body: received {0} of {1} bytes"
        raise ValueError(message.format(len(body), length))
    return length, body, tail
