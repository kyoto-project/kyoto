import inspect


def private(function):
  if not getattr(function, "private", False):
    function.private = True
  return function

def is_private(function):
  name = function.__name__
  if name.startswith("__"):
    return True
  else:
    return getattr(function, "private", False)

def blocking(function):
  if not getattr(function, "blocking", False):
    function.blocking = True
  return function

def is_blocking(function):
  return getattr(function, "blocking", False)


class Module(object):

  def __init__(self):
    """
    Module constructor
    """
    if not getattr(self, "register_as", None):
      self.register_as = self.__class__.__name__

  def methods(self, as_strings=True):
    """
    Returns all available module methods
    @as_strings: boolean, if true, returns tuple with method names,
    otherwise returns dictionary with method names as keys and function bodies as values
    """
    methods = inspect.getmembers(self, inspect.ismethod)
    methods = ((name, func) for name, func in methods if not is_private(func))
    if as_strings:
      methods = tuple(name for name, func in methods)
    else:
      methods = {name:func for name, func in methods}
    return methods
