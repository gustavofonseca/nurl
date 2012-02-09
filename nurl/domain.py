# coding: utf-8
import urllib2

from beaker.cache import cache_region
import base28
import pymongo

class ShortenGenerationError(Exception):
    def __init__(self, *args):
        super(ShortenGenerationError, self).__init__(*args)

class NotExists(Exception):
    def __init__(self, *args):
        super(NotExists, self).__init__(*args)

class ResourceGenerator(object):
    def __init__(self, request, generation_tool=base28):
        self._request = request
        self._generation_tool = generation_tool

    def generate(self, url):
        #generating index
        self._request.db['urls'].ensure_index('short_ref', unique=True)
        self._request.db['urls'].ensure_index('plain', unique=True)

        pre_fetch = self._request.db['urls'].find_one({'plain': url})
        if pre_fetch is not None:
            return pre_fetch['short_ref']

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
                return url_data['short_ref']

        raise ShortenGenerationError()

    @cache_region('long_term')
    def fetch(self, short_ref):
        fetched = self._request.db['urls'].find_one({'short_ref': short_ref})
        if fetched is None:
            raise NotExists()

        return fetched['plain']

class Url(object):
    def __init__(self, request, url=None, short_url=None, resource_gen=ResourceGenerator):

        if url is not None:
            check_whitelist = request.registry.settings.get('nurl.check_whitelist', False)
            if check_whitelist:
                url_domain = urllib2.Request(url).get_host()
                if url_domain not in request.registry.settings['nurl.whitelist']:
                    raise ValueError('Domain {} is not allowed'.format(url_domain))
            try:
                u = urllib2.urlopen(url)
            except urllib2.HTTPError:
                raise ValueError('Invalid Url')

        self._plain_url = url
        self._short_url = short_url
        self._request = request
        self._resource_generator = resource_gen(self._request)

    def shorten(self):
        if self._plain_url is None:
            raise AttributeError('Missing attribute url')
        short_ref = self._resource_generator.generate(self._plain_url)
        return self._request.route_url('shortened', short_ref=short_ref)

    def resolve(self):
        if self._short_url is None:
            raise AttributeError('Missing attribute short_url')
        return self._resource_generator.fetch(self._short_url)