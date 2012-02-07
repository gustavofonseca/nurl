import unittest

from pyramid import testing

from .domain import Url

class DummyResourceGen(object):
    def generate(self, url):
        return 'http://s.cl/4kgjc'

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
    def test_url_validation(self):

        valid_url = Url('http://www.scielo.br/scielo.php?script=sci_serial&pid=0100-879X&lng=en&nrm=iso')
        self.assertTrue(isinstance(valid_url, Url))

        #scielo web does not return 404 http error, we need to fix scielo web.
        notfound_url_param = Url('http://www.scielo.br/scielo.php?script=sci_serial&pid=0100-879XX&lng=en&nrm=iso')
        self.assertTrue(isinstance(notfound_url_param, Url))

        notfound_url_script = 'http://www.scielo.br/scielox.php?script=sci_serial&pid=0100-879XX&lng=en&nrm=iso'
        self.assertRaises(ValueError, Url, notfound_url_script)



    def test_shortening(self):

        valid_url = Url('http://www.scielo.br', resource_gen=DummyResourceGen)
        self.assertEqual(valid_url.shorten(), 'http://s.cl/4kgjc')
