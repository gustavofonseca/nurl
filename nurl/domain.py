# coding: utf-8
import urllib2

import base28
import pymongo

class ShortenGenerationError(Exception):
    def __init__(self, *args):
        super(ShortenGenerationError, self).__init__(*args)

class ResourceGenerator(object):
    def __init__(self, request, generation_tool=base28):
        self._request = request
        self._generation_tool = generation_tool

    def generate(self, url):
        #generating index
        self._request.db['urls'].ensure_index('short_ref', unique=True)

        attempts = 0
        while attempts < 10:
            weak_short_reference = self._generation_tool.genbase(5)
            url_data = {'plain': url, 'short_ref': weak_short_reference}
            try:
                self._request.db['urls'].insert(url_data, safe=True)
            except pymongo.errors.DuplicateKeyError:
                attempts += 1
                continue
            else:
                return 'http://s.cl/{}'.format(url_data['short_ref'])

        raise ShortenGenerationError()

class Url(object):
    def __init__(self, url, request, resource_gen=ResourceGenerator):
        try:
            u = urllib2.urlopen(url)
        except urllib2.HTTPError:
            raise ValueError('Invalid Url')

        self._plain_url = url
        self._request = request
        self._resource_generator = resource_gen(self._request)

    def shorten(self):
        return self._resource_generator.generate(self._plain_url)

