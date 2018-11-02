import json
import urllib3
from .exceptions import CamaraDeputadosConnectionError, CamaraDeputadosInvalidResponse


class APIData(object):
    """ Parent class for API calls
    """

    def __init__(self, api_section):
        self.camara_dos_deputados_endpoint = 'https://dadosabertos.camara.leg.br/api/v2/'
        self.http = urllib3.PoolManager()
        self._api_section = api_section

    def runThroughAllPages(self, *args, **kwargs):
        data_length = None
        page_num = 1
        url_args = kwargs
        if len(args):
            url_path = '{}{}/{}{}'.format(
                self.camara_dos_deputados_endpoint,
                self._api_section,
                args[0],
                '/{}'.format(args[1]) if len(args) > 1 else ''
            )
        else:
            url_path = '{}{}'.format(self.camara_dos_deputados_endpoint, self._api_section)
        while data_length != 0:
            url_args['pagina'] = str(page_num)
            r = self.http.request(
                'GET',
                url_path,
                fields=url_args,
                headers={'accept': 'application/json'}
            )
            if r.status != 200:
                raise CamaraDeputadosConnectionError(url_path, r.status)
            
            try:
                page = json.loads(r.data.decode('utf-8'))
                data_length = len(page['dados'])
                dados = page['dados']
            except:
                raise CamaraDeputadosInvalidResponse(r.data.decode('utf-8'))
            yield dados
            page_num += 1

    def getAPISingleRequest(self, param_id, param_page = ''):
        if param_page:
            param_page = '/{}'.format(param_page)
        url = '{}{}/{}{}'.format(
            self.camara_dos_deputados_endpoint,
            self._api_section,
            param_id,
            param_page
        )
        r = self.http.request(
            'GET',
            url,
            headers={'accept': 'application/json'}
        )
        if r.status != 200:
            raise CamaraDeputadosConnectionError(url, r.status)
        try:
            return json.loads(r.data.decode('utf-8'))['dados']
        except:
            raise CamaraDeputadosInvalidResponse(r.data.decode('utf-8'))

    def getJSONFrom(self, uri, **kwargs):
        r = self.http.request(
            'GET',
            uri,
            fields=kwargs,
            headers={'accept': 'application/json'}
        )
        if r.status != 200:
            raise CamaraDeputadosConnectionError(uri, r.status)
        try:
            return json.loads(r.data.decode('utf-8'))
        except:
            raise CamaraDeputadosInvalidResponse(r.data.decode('utf-8'))
