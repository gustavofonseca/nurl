# coding: utf-8
import urllib2
import base28

class ResourceGenerator(object):
    def generate(self, url):
        pass

class Url(object):
    def __init__(self, url, resource_gen=ResourceGenerator):
        try:
            u = urllib2.urlopen(url)
        except urllib2.HTTPError:
            raise ValueError('Invalid Url')

        self._plain_url = url
        self._resource_generator = resource_gen()

    def shorten(self):
        return self._resource_generator.generate(self._plain_url)

