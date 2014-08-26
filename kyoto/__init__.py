__version__ = "0.1.0"


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
