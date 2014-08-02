import os
import importlib
from kyoto.conf import default_settings
SETTINGS_MODULE = os.environ.get("KYOTO_SETTINGS_MODULE", None)


class Settings(object):

    def __init__(self):
        for key in dir(default_settings):
            self.__dict__[key] = getattr(default_settings, key)
        if SETTINGS_MODULE:
            try:
                settings_module = importlib.import_module(SETTINGS_MODULE)
            except ImportError:
                message = "Could not import settings module: '{0}'"
                raise ImportError(message.format(settings))
            else:
                for key in dir(settings_module):
                    if key.isupper():
                        value = getattr(settings_module, key)
                        if not callable(value):
                            self.__dict__[key] = value

settings = Settings()
