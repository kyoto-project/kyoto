import kyoto
import types
import inspect


def get_module_name(module):
    return module.__name__.split(".")[-1]


def is_callable_object(obj):
    """
    Predicate, that returns positive response, if @obj is callable object, e.g.
    Named function, anonymous function, class method and so on
    """
    return isinstance(obj, (types.FunctionType, types.MethodType,
                            types.BuiltinFunctionType, types.BuiltinMethodType))


def get_module_functions(module, as_strings=True):
    """
    Returns all public module functions
    """
    functions = inspect.getmembers(module, is_callable_object)
    functions = ((k, v) for k, v in functions if not kyoto.is_private(v))
    if as_strings:
        functions = tuple(name for name, _ in functions)
    else:
        functions = {name: func for name, func in functions}
    return functions
