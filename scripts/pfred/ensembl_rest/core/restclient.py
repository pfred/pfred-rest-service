"""

This file is part of pyEnsembl.
    Derived from a file in the RESTEasy project by Arijit Basu <sayanarijit@gmail.com>.
    Copyright (C) 2018, Andrés García

    Any questions, comments or issues can be addressed to a.garcia230395@gmail.com.

"""

from __future__ import absolute_import, unicode_literals
import json
import requests
from simplejson.decoder import JSONDecodeError
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class HTTPError(Exception):
    def __init__(self, response):
        self.response = response
        try:
            Exception.__init__(self, 'Server returned HTTP status code: %s\nContent: %s' % (response.status_code, response.json()))
        except JSONDecodeError:
            Exception.__init__(self, 'Server returned HTTP status code: %s\nContent: %s' % (response.status_code, response.text))

class InvalidResponseError(Exception):
    def __init__(self, response):
        self.response = response
        try:
            Exception.__init__(self, 'Server returned incompatible response:\n', response.json())
        except JSONDecodeError:
            Exception.__init__(self, 'Server returned incompatible response:\n', response.text)


class RESTClient:
    """
    REST session creator
    """
    def __init__(self, base_url, auth=None, verify=False, cert=None, timeout=None,
                 encoder=json.dumps, decoder=json.loads, debug=False):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.auth = auth
        self.session.verify = verify
        self.session.cert = cert
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.timeout = timeout
        self.encoder = encoder
        self.decoder = decoder
        self.debug = debug

    def route(self, *args):
        """
        Return endpoint object
        """
        return APIEndpoint(
            endpoint=self.base_url + '/' + ('/'.join(map(str, args))),
            session=self.session, timeout=self.timeout,
            encoder=self.encoder, decoder=self.decoder, debug=self.debug
        )


class APIEndpoint(object):
    """
    API endpoint
    """
    def __init__(self, endpoint, session, timeout=None,
                 encoder=json.dumps, decoder=json.loads, debug=False):
        self.endpoint = endpoint
        self.session = session
        self.timeout = timeout
        self.encoder = json.dumps
        self.decoder = json.loads
        self.debug = debug
        self.last_response = None
    # ---

    def route(self, *args):
        """
        Return endpoint object
        """
        return APIEndpoint(
            endpoint=self.endpoint + '/' + ('/'.join(map(str, args))),
            session=self.session, timeout=self.timeout,
            encoder=self.encoder, decoder=self.decoder, debug=self.debug
        )
    # ---

    def do(self, method, params=None, **kwargs):
        """
        Do the HTTP request
        """
        method = method.upper()
        adapter = requests.adapters.HTTPAdapter(pool_maxsize=100)
        self.session.mount('https://', adapter)

        if self.debug:
            return dict(endpoint=self.endpoint, method=method, kwargs=kwargs, session=self.session)

        if method == 'GET':
            response = self.session.get(self.endpoint,
                                        params=params,
                                        timeout=self.timeout,
                                        **kwargs)
        else:
            response = self.session.request(method, self.endpoint,
                    data=self.encoder(params), params=params, timeout=self.timeout, **kwargs)
            
        content = response.content.decode('UTF-8')
        if response.status_code not in range(200,300):
            raise HTTPError(response)

        try:
            return self.decoder(content)
        except Exception:
            return content
    # ---

    def get(self, **kwargs): return self.do('GET', **kwargs)
    def post(self, **kwargs): return self.do('POST', **kwargs)
    def put(self, **kwargs): return self.do('PUT', **kwargs)
    def patch(self, **kwargs): return self.do('PATCH', **kwargs)
    def delete(self, **kwargs): return self.do('DELETE', **kwargs)
