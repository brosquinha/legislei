from time import sleep

import certifi
import urllib3
from urllib3.request import urlencode

class Base(object):
    """
    Classe base de operações de rede
    """

    def __init__(self):
        self.http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where()
        )

    def _make_request(self, *args, **kwargs):
        """
        Faz requisições HTTP

        Se receber um 429, espera 50ms e depois tenta de novo.

        :param args: Unamed args for urllib3 request
        :param kwagargs: Named args for urllib3 request
        :return: Request object
        """
        too_many_requests = True
        while too_many_requests:
            r = self.http.request(*args, **kwargs)
            if r.status == 429:
                sleep(0.05)
            else:
                return r

    def _build_url(self, base_url, query_args):
        """
        Builds a URL string with given query parameters

        :param base_url: URL base
        :type base_url: String
        :param query_args: URL Query parameters
        :type query_args: Dict
        :returns: URL with query parameters
        :rtype: String
        """
        return '{}?{}'.format(base_url, urlencode(query_args))
