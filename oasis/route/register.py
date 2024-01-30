import functools
import importlib
import logging
import re

from typing import Callable
from functools import partial

from oasis.settings.conf import HANDLERS_DIR

REGISTERED_ROUTES = {}
MATCHING_PATTERNS = {
    '<int>': r'\d+',
    '<str>': r'\w+'
}


logger = logging.getLogger('Handlers Registration')


def split_route(route: str):

    return re.split('\/', route)


def find_route(client_route):

    client_route = split_route(client_route)

    for route in REGISTERED_ROUTES:
        rt = split_route(route)

        if len(rt) != len(client_route):
            continue

        func_args = []
        for idx in range(len(rt)):
            if rt[idx] in MATCHING_PATTERNS:
                match = re.match(MATCHING_PATTERNS.get(rt[idx]), client_route[idx])
                if not match:
                    break
                else:
                    func_args.append(match.group())
                    continue
            if rt[idx] != client_route[idx]:
                break
        else:
            logger.info('Found route with args %s.' % func_args)
            return route, func_args
    else:
        return


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

