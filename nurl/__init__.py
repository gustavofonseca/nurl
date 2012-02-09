import os

from pyramid.config import Configurator
from pyramid.events import NewRequest
import pymongo

APP_PATH = os.path.abspath(os.path.dirname(__file__))

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)

    db_uri = settings['db_uri']
    conn = pymongo.Connection(db_uri)
    config.registry.settings['db_conn'] = conn

    try:
        with open(os.path.join(APP_PATH, '..' ,'domain_whitelist.txt'), 'r') as whitelist:
            config.registry.settings['nurl.whitelist'] = set((domain for domain in whitelist))
    except IOError:
        config.registry.settings['nurl.check_whitelist'] = False

    config.add_subscriber(add_mongo_db, NewRequest)

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('shortened', '/{short_ref}')

    #rest api version 0.1
    config.add_route('shortener_v01', '/api/v0.1/shorten')

    config.scan()
    return config.make_wsgi_app()

def add_mongo_db(event):
    settings = event.request.registry.settings
    db = settings['db_conn'][settings['db_name']]
    event.request.db = db
