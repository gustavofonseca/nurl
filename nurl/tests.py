import unittest
import logging

from pyramid import testing

from .domain import Url
from .domain import ResourceGenerator

ENABLE_LOGGING = True
logging.basicConfig(filename='nurl.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def log_messages(func):
    def decorated(*args, **kwargs):
        if ENABLE_LOGGING:
            logging.info('{0} -> args: {1}, kwargs: {2}'.format(
                func.__name__, repr(args), repr(kwargs)))
        func(*args, **kwargs)
    return decorated

class DummyResourceGen(object):
    def __init__(self, request):
        pass

    def generate(self, url):
        return '4kgjc'

    def fetch(self, short_ref):
        return 'http://www.scielo.br'

class DummyBase28(object):
    @staticmethod
    def genbase(size):
        return '4kgjc'

class DummyMongoDB(object):
    def __getitem__(self, key):
        return self

    @log_messages
    def ensure_index(self, *args, **kwargs):
        return self

    @log_messages
    def insert(self, *args, **kwargs):
        return self

    @log_messages
    def find_one(self, *args, **kwargs):
        """
        This function will be added to a DummyMongoDB
        instance via monkey patch.
        """
        return None

class DummyMongoDB_2(object):
    """
    Use this instance on cases where you
    want the method ``find_one`` to return
    some values.
    """
    def __getitem__(self, key):
        return self

    @log_messages
    def ensure_index(self, *args, **kwargs):
        return self

    def find_one(self,  *args, **kwargs):
        """
        Must discover why this method does not work
        correctly when decorated with ``@log_messages``.

        The short_ref is a little different to ensure
        the value returned by ResourceGenerator.generate
        was retrieved from mongodb.
        """
        if ENABLE_LOGGING:
            logging.info('{0} -> args: {1}, kwargs: {2}'.format(
                'find_one', repr(args), repr(kwargs)))

        if args[0].has_key('plain'):
            return {'short_ref': '4kgxx',}
        elif args[0].has_key('short_ref') and args[0]['short_ref'] == 'http://s.cl/4kgxx':
            return {'plain': 'http://www.scielo.br',}
        else:
            None

class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_home(self):
        from .views import home

        request = testing.DummyRequest()
        info = home(request)
        self.assertEqual(info['project'], 'nurl')
        self.assertFalse(info.has_key('short_url'))

    def test_shortening_success(self):
        from .views import home

        request = testing.DummyRequest()
        request.params = {'url': 'http://www.scielo.br'}
        request.route_url = lambda *args, **kwargs: 'http://s.cl/4kgjc'
        request.db = DummyMongoDB()
        info = home(request)
        self.assertTrue(info.has_key('short_url'))

    def test_shortening_missing(self):
        from .views import url_shortener
        from pyramid.httpexceptions import HTTPBadRequest

        request = testing.DummyRequest()
        self.assertRaises(HTTPBadRequest, url_shortener, request)

    def test_shortening_invalid(self):
        from .views import url_shortener
        from pyramid.httpexceptions import HTTPBadRequest

        request = testing.DummyRequest()
        request.params = {'url': 'http://www.scielo.br/scielox.php?script=sci_serial&pid=0100-879XX&lng=en&nrm=iso'}
        self.assertRaises(HTTPBadRequest, url_shortener, request)

    def test_resolving_notfound(self):
        from .views import short_ref_resolver
        from pyramid.httpexceptions import HTTPNotFound

        request = testing.DummyRequest()
        request.matchdict = {'short_ref': '4kgxx'}
        request.db = DummyMongoDB()
        self.assertRaises(HTTPNotFound, short_ref_resolver, request)

    def test_resolving_success(self):
        from .views import short_ref_resolver
        from pyramid.httpexceptions import HTTPMovedPermanently

        request = testing.DummyRequest()
        request.matchdict = {'short_ref': 'http://s.cl/4kgxx'}
        request.db = DummyMongoDB_2()
        self.assertRaises(HTTPMovedPermanently, short_ref_resolver, request)

class DomainTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def required_settings(self):
        return {'cache.regions': 'long_term',
                'cache.type': 'memory',
                'cache.long_term.expire': '3600',
                }


    def test_url_validation(self):
        request = testing.DummyRequest()
        valid_url = Url(request, url='http://www.scielo.br/scielo.php?script=sci_serial&pid=0100-879X&lng=en&nrm=iso')
        self.assertTrue(isinstance(valid_url, Url))

        #scielo web does not return 404 http error, we need to fix scielo web.
        notfound_url_param = Url(request, url='http://www.scielo.br/scielo.php?script=sci_serial&pid=0100-879XX&lng=en&nrm=iso')
        self.assertTrue(isinstance(notfound_url_param, Url))

        notfound_url_script = 'http://www.scielo.br/scielox.php?script=sci_serial&pid=0100-879XX&lng=en&nrm=iso'
        self.assertRaises(ValueError, Url, request, url=notfound_url_script)

    def test_shortening(self):
        request = testing.DummyRequest()
        request.route_url = lambda *args, **kwargs: 'http://s.cl/4kgjc'
        valid_url = Url(request, url='http://www.scielo.br', resource_gen=DummyResourceGen)
        self.assertEqual(valid_url.shorten(), 'http://s.cl/4kgjc')

    def test_resource_generation(self):
        request = testing.DummyRequest()
        request.db = DummyMongoDB()

        resource_gen = ResourceGenerator(request, generation_tool=DummyBase28)
        url = 'http://www.scielo.br'
        self.assertEqual(resource_gen.generate(url), '4kgjc')

    def test_resource_generation_existing(self):
        request = testing.DummyRequest()
        request.db = DummyMongoDB_2()

        resource_gen = ResourceGenerator(request, generation_tool=DummyBase28)
        url = 'http://www.scielo.br'
        self.assertEqual(resource_gen.generate(url), '4kgxx')

    def test_resource_generation_fetch_short_refs(self):
        from pyramid_beaker import set_cache_regions_from_settings
        from .domain import NotExists

        request = testing.DummyRequest()
        request.db = DummyMongoDB_2()

        settings = self.required_settings()
        set_cache_regions_from_settings(settings) #setting cache_regions

        resource_gen = ResourceGenerator(request, generation_tool=DummyBase28)
        short_ref = 'http://s.cl/4kgxx'
        self.assertEqual(resource_gen.fetch(short_ref), 'http://www.scielo.br')

        short_ref = 'http://s.cl/4kgxy'
        self.assertRaises(NotExists, resource_gen.fetch, short_ref)

    def test_resolving(self):
        request = testing.DummyRequest()
        valid_url = Url(request, short_url='http://s.cl/4kgxx', resource_gen=DummyResourceGen)
        self.assertEqual(valid_url.resolve(), 'http://www.scielo.br')

    def test_whitelist(self):
        request = testing.DummyRequest()
        request.route_url = lambda *args, **kwargs: 'http://s.cl/4kgjc'
        class DummyRegistry(dict):
            def __init__(self):
                self.settings = {}
        request.registry = DummyRegistry()
        request.registry.settings.update({'nurl.check_whitelist': True})
        request.registry.settings.update({'nurl.whitelist': ['www.google.com']})

        self.assertRaises(ValueError, Url, request, url='http://www.scielo.br', resource_gen=DummyResourceGen)

        request.registry.settings.update({'nurl.whitelist': ['www.scielo.br']})
        valid_url = Url(request, url='http://www.scielo.br', resource_gen=DummyResourceGen)
        self.assertEqual(valid_url.shorten(), 'http://s.cl/4kgjc')