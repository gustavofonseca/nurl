import os

from pyramid.config import Configurator
from pyramid.events import NewRequest
from pyramid_beaker import set_cache_regions_from_settings
from pyramid.renderers import JSONP
from pyramid.settings import asbool
import pymongo
import newrelic.agent

APP_PATH = os.path.abspath(os.path.dirname(__file__))


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    set_cache_regions_from_settings(settings)
    config = Configurator(settings=settings)

    db_uri = settings['mongodb.db_uri']
    conn = pymongo.Connection(db_uri)
    config.registry.settings['db_conn'] = conn

    try:
        if asbool(settings.get('nurl.check_whitelist', False)):
            with open(os.path.join(APP_PATH, '..' ,'whitelist.txt')) as whitelist:
                config.registry.settings['nurl.whitelist'] = get_whitelist(whitelist,
                    asbool(settings.get('nurl.check_whitelist_auto_www', False)))
    except IOError:
        config.registry.settings['nurl.check_whitelist'] = False

    config.add_subscriber(add_mongo_db, NewRequest)

    config.add_renderer('jsonp', JSONP(param_name='callback'))

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('shortened', '/{short_ref}')

    #rest api version 1
    config.add_route('shortener_v1', '/api/v1/shorten')

    config.scan()
    application = config.make_wsgi_app()

    #newrelic agent
    try:
        if asbool(settings.get('newrelic.enable', False)):
            newrelic.agent.initialize(os.path.join(APP_PATH, '..', 'newrelic.ini'),
                settings['newrelic.environment'])
            return newrelic.agent.wsgi_application()(application)
        else:
            return application
    except IOError:
        config.registry.settings['newrelic.enable'] = False
        return application

def add_mongo_db(event):
    settings = event.request.registry.settings
    db = settings['db_conn'][settings['mongodb.db_name']]
    event.request.db = db

def get_whitelist(whitelist, auto_www=False):
    if auto_www:
        hostnames = []
        for host in whitelist:
            hostnames.append(host.strip('\n'))
            if not host.startswith('www'):
                hostnames.append('www.' + host.strip('\n'))
        return set(hostnames)
    else:
        return set((host.strip('\n') for host in whitelist))




