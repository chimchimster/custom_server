from oasis.http.utils.render import render
from oasis.route.register import register


@register(route='/')
def main(request):

    return render('base.html')


@register(route='/index/')
def index(request):

    return render('index.html')


@register(route='/index/<int>/')
def index_for_id(request, some_id):

    return render('index.html')


__all__ = [
    'main',
    'index',
    'index_for_id',
]