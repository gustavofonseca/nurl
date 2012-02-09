from .domain import Url
from .domain import ShortenGenerationError

from pyramid.view import view_config
from pyramid.response import Response
from pyramid import httpexceptions

@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project':'nurl'}

@view_config(route_name='shortener')
def url_shortener(request):

    incoming_url = request.params.get('url')
    if incoming_url is None:
        raise httpexceptions.HTTPBadRequest()

    url_handler = Url(request, url=incoming_url)
    try:
        short_url = url_handler.shorten()
    except ShortenGenerationError:
        raise httpexceptions.HTTPInternalServerError()

    return Response(short_url)
