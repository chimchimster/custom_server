from oasis.settings.conf import TEMPLATES_DIR
from oasis.exceptions.exc import TemplatesNotFound


def render(template_name: str):

    if not TEMPLATES_DIR.exists() or not TEMPLATES_DIR.is_dir():
        raise TemplatesNotFound('Can not find templates directory.')

    for template in TEMPLATES_DIR.iterdir():
        if str(template).endswith(template_name):
            with open(template, 'rb') as html_page:
                return html_page.read()

    raise TemplatesNotFound('Can not find templates directory.')

