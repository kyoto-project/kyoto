import inspect


def private(function):
    """
    Marks given function as private
    (which'll be not accessible outside of this module)
    """
    if not getattr(function, "private", False):
        function.private = True
    return function


def is_private(function):
    """
    Returns true if given function is a private
    """
    name = function.__name__
    if name.startswith("__"):
        return True
    else:
        return getattr(function, "private", False)


def blocking(function):
    """
    Marks given function as blocking (which'll be executed in another thread)
    """
    if not getattr(function, "blocking", False):
        function.blocking = True
    return function


def is_blocking(function):
    """
    Returns true if function is marked as blocking
    """
    return getattr(function, "blocking", False)


class Module(object):

    register_as = None

    def __init__(self):
        """
        Module constructor
        """
        if not self.register_as:
            self.register_as = self.__class__.__name__

    def methods(self, as_strings=True):
        """
        Returns all public module methods
        """
        methods = inspect.getmembers(self, inspect.ismethod)
        methods = ((name, func)
                   for name, func in methods if not is_private(func))
        if as_strings:
            methods = tuple(name for name, func in methods)
        else:
            methods = {name: func for name, func in methods}
        return methods
