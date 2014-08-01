import os
import multiprocessing
import concurrent.futures


"""
Common settings
"""

HOSTNAME = os.environ.get("KYOTO_HOSTNAME", "localhost")
PORT = os.environ.get("KYOTO_PORT", 1337)
BIND_ADDRESS = (HOSTNAME, PORT)

INSTALLED_MODULES = ()


"""
Network settings
"""

MAX_BERP_SIZE = 33554432 # 32 megabytes
READ_CHUNK_SIZE = 65536 # 64 kilobytes
COMPRESS_RESPONSE = False
DISABLE_NAGLE = True

"""
Logging settings
"""

LOGGING = {
  "version": 1,
  "disable_existing_loggers": False,

  "formatters": {
    "standard": {
      "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    },
  },
  "handlers": {
    "default": {
      "level":"INFO",
      "class":"logging.StreamHandler",
    },
  },
  "loggers": {
    "": {
      "handlers": ["default"],
      "level": "INFO",
      "propagate": True
    }
  }
}


"""
Blocking I/O related settings
"""

# list of modules which must be monkey-patched by gevent
GEVENT_PATCH_MODULES = (
  "os",
  "ssl",
  "time",
  "select",
  "socket",
)

BLOCKING_POOL_SIZE = getattr(os, "cpu_count", multiprocessing.cpu_count)()
BLOCKING_POOL_CLASS = concurrent.futures.ThreadPoolExecutor
BLOCKING_POOL = BLOCKING_POOL_CLASS(max_workers=BLOCKING_POOL_SIZE)
