from .domain import Url
from .domain import ShortenGenerationError

from pyramid.view import view_config
from pyramid.response import Response
from pyramid import httpexceptions

@view_config(route_name='home', renderer='templates/home.pt')
def home(request):

    response_dict = {'project':'nurl'}

    incoming_url = request.params.get('url')
    if incoming_url is not None:
        short_url = url_shortener(request).text
        response_dict.update({'short_url': short_url})

    return response_dict

@view_config(route_name='shortener_v01')
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
