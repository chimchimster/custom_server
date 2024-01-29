import functools
from typing import Callable
from functools import partial


REGISTERED_ROUTES = {}


def register(route='/'):
    def wrap_outter(func: Callable):
        @functools.wraps(func)
        def wrap_inner(*args, **kwargs):

            REGISTERED_ROUTES[route] = partial(func, *args, **kwargs)

        return wrap_inner

    return wrap_outter

