from oasis.http.utils.render import render
from oasis.route.register import register


@register(route='/')
def main():

    return render('base.html')


@register(route='/index')
def index():

    return render('index.html')


__all__ = [
    'main',
    'index',
]