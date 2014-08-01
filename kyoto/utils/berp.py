import struct
import kyoto.conf


class MaxBERPLengthError(Exception):
  pass


def pack(message):
  if not isinstance(message, bytes):
    message = message.encode("utf-8")
  return struct.pack('>I', len(message)) + message

def unpack(message):
  head, tail = message[:4], message[4:]
  if len(head) == 4:
    length, = struct.unpack('>I', head)
  else:
    raise ValueError("Incomplete BERP head: received {0} of 4 bytes".format(len(head)))
  if length > kyoto.conf.settings.MAX_BERP_SIZE:
    raise MaxBERPLengthError("Invalid BERP length: {0}/{1}".format(kyoto.conf.settings.MAX_BERP_SIZE, length))
  body, tail = tail[:length], tail[length:]
  if len(body) < length:
    raise ValueError("Incomplete BERP body: received {0} of {1} bytes".format(len(body), length))
  return length, body, tail
