import importlib
import logging
import pathlib

path = pathlib.Path().resolve() / 'oasis' / 'handlers'

logger = logging.getLogger('Handlers Registration')


def register_all():

    if path.is_dir():
        for module_path in path.iterdir():
            module_name = module_path.stem

            try:
                module = importlib.import_module('oasis.handlers.%s' % module_name)
                for name in dir(module):
                    function = getattr(module, name)
                    if callable(function):
                        function()
            except ImportError:
                logger.critical('Can not found module to load.')