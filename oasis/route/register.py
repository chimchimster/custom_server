import functools
import importlib
import logging

from typing import Callable
from functools import partial

from oasis.settings.conf import HANDLERS_DIR

REGISTERED_ROUTES = {}


logger = logging.getLogger('Handlers Registration')


def register(route='/'):
    def wrap_outter(func: Callable):
        @functools.wraps(func)
        def wrap_inner(*args, **kwargs):

            REGISTERED_ROUTES[route] = partial(func, *args, **kwargs)

        return wrap_inner

    return wrap_outter


def register_all():

    if HANDLERS_DIR.is_dir():
        for module_path in HANDLERS_DIR.iterdir():
            module_name = module_path.stem
            try:
                module = importlib.import_module('oasis.handlers.%s' % module_name)
                for name in getattr(module, '__all__', []):
                    function = getattr(module, name)
                    if callable(function):
                        function()
            except ImportError:
                logger.critical('Can not found module to load.')