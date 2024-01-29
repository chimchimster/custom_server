import pathlib

from oasis.settings.conf import TEMPLATES_DIR
from oasis.exceptions.exc import TemplatesNotFound


def render(template_name: str, directory: pathlib.Path = TEMPLATES_DIR):

    if not TEMPLATES_DIR.exists() or not TEMPLATES_DIR.is_dir():
        raise TemplatesNotFound('Can not find templates directory.')

    for template in directory.iterdir():
        if template.is_dir():
            return render(template_name, template)
        elif str(template).endswith(template_name):
            with open(template, 'rb') as html_page:
                return html_page.read()

    raise TemplatesNotFound('Can not find template.')

