import json

from .api import Base
from .exceptions import (CamaraDeputadosConnectionError,
                         CamaraDeputadosInvalidResponse)


class RESTful(Base):
    """
    Classe base de operações da API REST da Câmara de Deputados

    Essa classe contém métodos base para chamadas da API REST da Câmera dos Deputados, \
    herdade pelas demais classes do pacote.

    :param api_section: Seção da API da CM (i.g. deputados, eventos, etc)
    :type api_section: String
    """

    def __init__(self, api_section):
        super().__init__()
        self.camara_dos_deputados_endpoint = 'https://dadosabertos.camara.leg.br/api/v2/'
        self._api_section = api_section

    def runThroughAllPages(self, *args, **kwargs):
        """
        Obtém todas as páginas de um endpoint

        Essa função obtém todas as páginas de um endpoint definido pela seção \
        definida no construtor da classe, bem como a lista argumentos passados \
        para essa função. Essa função utiliza o parâmetro `pagina` disponível em \
        todas as chamadas da API da Câmara dos Deputados que utilizam paginação. \
        Retorna um Generator para cada página obtida.

        :return: Generator de páginas da chamada
        :rtype: Generator
        :raises: CamaraDeputadosConnectionError, CamaraDeputadosInvalidResponse
        """
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
            r = self._make_request(
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
        """
        Retorna dados de um endpoint

        Retorna os dados de uma única chamada à API. Normalmente utilizada para \
        buscar dados de uma entidade definida pelo id passado em `param_id`, como, \
        por exemplo, um deputado ou uma proposição.

        :param param_id: Id da entidade
        :type param_id: String
        :param param_page: Subpágina da API
        :type param_page: String
        :return: Dados da API
        :rtype: Dictionary
        :raises: CamaraDeputadosConnectionError, CamaraDeputadosInvalidResponse
        """
        if param_page:
            param_page = '/{}'.format(param_page)
        url = '{}{}/{}{}'.format(
            self.camara_dos_deputados_endpoint,
            self._api_section,
            param_id,
            param_page
        )
        r = self._make_request(
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
        """
        Obtém dados diretamente da URL fornecida

        Esse método recebe uma URL e processa o JSON dela. Recebe parâmetros \
        com chaves como parâmetros GET da chamada.

        :param uri: URL de chamada
        :type uri: String
        :return: Dados JSON processados
        :rtype: Dictionary
        :raises: CamaraDeputadosConnectionError, CamaraDeputadosInvalidResponse
        """
        r = self._make_request(
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
