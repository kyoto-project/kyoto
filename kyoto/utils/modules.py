import kyoto
import inspect


def get_module_name(module):
    return module.__name__.split(".")[-1]


def get_module_functions(module, as_strings=True):
    """
    Returns all public module functions
    """
    functions = inspect.getmembers(module, inspect.isfunction)
    functions = ((k, v) for k, v in functions if not kyoto.is_private(v))
    if as_strings:
        functions = tuple(name for name, _ in functions)
    else:
        functions = {name: func for name, func in functions}
    return functions
