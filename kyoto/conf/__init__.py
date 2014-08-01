import os
import importlib

from kyoto.conf import default_settings


class Settings(object):

  def __init__(self):
    settings_module = os.environ.get("KYOTO_SETTINGS_MODULE", "kyoto.conf.default_settings")
    for key in dir(default_settings):
      self.__dict__[key] = getattr(default_settings, key)
    try:
      settings_module = importlib.import_module(settings_module)
    except ImportError:
      raise ImportError("Could not import settings module: '{0}'".format(settings))
    else:
      for key in dir(settings_module):
        if key.isupper():
          value = getattr(settings_module, key)
          if not callable(value):
            self.__dict__[key] = value

settings = Settings()
