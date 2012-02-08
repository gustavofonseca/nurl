import unittest

from pyramid import testing

from .domain import Url
from .domain import ResourceGenerator

class DummyResourceGen(object):
    def __init__(self, request):
        pass

    def generate(self, url):
        return 'http://s.cl/4kgjc'

class DummyBase28(object):
    @staticmethod
    def genbase(size):
        return '4kgjc'

class DummyMongoDB(object):
    def __getitem__(self, key):
        return self

    def ensure_index(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        return self

class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_my_view(self):
        from .views import my_view
        request = testing.DummyRequest()
        info = my_view(request)
        self.assertEqual(info['project'], 'nurl')

class DomainTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_url_validation(self):
        request = testing.DummyRequest()
        valid_url = Url('http://www.scielo.br/scielo.php?script=sci_serial&pid=0100-879X&lng=en&nrm=iso', request)
        self.assertTrue(isinstance(valid_url, Url))

        #scielo web does not return 404 http error, we need to fix scielo web.
        notfound_url_param = Url('http://www.scielo.br/scielo.php?script=sci_serial&pid=0100-879XX&lng=en&nrm=iso', request)
        self.assertTrue(isinstance(notfound_url_param, Url))

        notfound_url_script = 'http://www.scielo.br/scielox.php?script=sci_serial&pid=0100-879XX&lng=en&nrm=iso'
        self.assertRaises(ValueError, Url, notfound_url_script, request)

    def test_shortening(self):
        request = testing.DummyRequest()
        valid_url = Url('http://www.scielo.br', request, resource_gen=DummyResourceGen)
        self.assertEqual(valid_url.shorten(), 'http://s.cl/4kgjc')

    def test_resource_generation(self):
        request = testing.DummyRequest()
        request.db = DummyMongoDB()
        resource_gen = ResourceGenerator(request, generation_tool=DummyBase28)
        url = 'http://www.scielo.br'
        self.assertEqual(resource_gen.generate(url), 'http://s.cl/4kgjc')

