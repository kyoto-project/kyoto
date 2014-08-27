import os
import multiprocessing
import concurrent.futures
import kyoto.network.connection


"""
Common settings
"""

INSTALLED_MODULES = ()

"""
Network settings
"""

BIND_HOSTNAME = os.environ.get("KYOTO_HOSTNAME", "localhost")
BIND_PORT = os.environ.get("KYOTO_PORT", 1337)
BIND_ADDRESS = (BIND_HOSTNAME, BIND_PORT)

MAX_BERP_SIZE = 33554432  # 32 megabytes
READ_CHUNK_SIZE = 65536  # 64 kilobytes
COMPRESS_RESPONSE = False
DISABLE_NAGLE = True
CONNECTION_TIMEOUT = 10 # in seconds
CONNECTION_MANAGER_CLASS = kyoto.network.connection.SingleConnectionManager

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
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
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


# list of modules which must be monkey-patched by gevent
GEVENT_PATCH_MODULES = (
    "os",
    "ssl",
    "time",
    "select",
    "socket",
)

"""
Blocking I/O settings
"""

BLOCKING_POOL_SIZE = getattr(os, "cpu_count", multiprocessing.cpu_count)()
BLOCKING_POOL_CLASS = concurrent.futures.ThreadPoolExecutor
BLOCKING_POOL = BLOCKING_POOL_CLASS(max_workers=BLOCKING_POOL_SIZE)
