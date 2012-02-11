# coding: utf-8

# Copyright (c) 2012, Gustavo Fonseca <gustavofons@gmail.com>
# All rights reserved.

# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:

#     Redistributions of source code must retain the above copyright notice, this
#     list of conditions and the following disclaimer.

#     Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.

#     Neither the name of the copyright holder nor the names of its contributors
#     may be used to endorse or promote products derived from this software without
#     specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
# OF SUCH DAMAGE.

import urllib2

from beaker.cache import cache_region
from beaker.cache import region_invalidate
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
        self._digit_count = int(self._request.registry.settings.get('nurl.digit_count', 5))

    @cache_region('seconds')
    def generate(self, url):
        #generating index
        self._request.db['urls'].ensure_index('short_ref', unique=True)
        self._request.db['urls'].ensure_index('plain', unique=True)

        pre_fetch = self._request.db['urls'].find_one({'plain': url})
        if pre_fetch is not None:
            return pre_fetch['short_ref']

        attempts = 0
        while attempts < 10:
            weak_short_reference = self._generation_tool.genbase(self._digit_count)
            url_data = {'plain': url, 'short_ref': weak_short_reference}
            try:
                self._request.db['urls'].insert(url_data, safe=True)
            except pymongo.errors.DuplicateKeyError:
                attempts += 1
                continue
            else:
                region_invalidate(self.fetch, None, url_data['short_ref'])
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
                url_domain = '.'.join(urllib2.Request(url).get_host().split('.')[-2:])
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