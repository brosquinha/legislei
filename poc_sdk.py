import json
import urllib3

camara_dos_deputados_endpoint = 'https://dadosabertos.camara.leg.br/api/v2/'

class APIData():

    def __init__(self, api_section):
        self.http = urllib3.PoolManager()
        self._api_section = api_section

    def runThroughAllPages(self, *args, **kwargs):
        data_length = None
        page_num = 1
        url_args = kwargs
        if len(args):
            url_path = '{}{}/{}{}'.format(
                camara_dos_deputados_endpoint,
                self._api_section,
                args[0],
                '/{}'.format(args[1]) if len(args) > 1 else ''
            )
        else:
            url_path = '{}{}'.format(camara_dos_deputados_endpoint, self._api_section)
        while data_length != 0:
            url_args['pagina'] = str(page_num)
            r = self.http.request(
                'GET',
                url_path,
                fields=url_args,
                headers={'accept': 'application/json'}
            )
            if r.status != 200:
                raise Exception('API call failed: {}'.format(url_args))
            
            try:
                page = json.loads(r.data.decode('utf-8'))
                data_length = len(page['dados'])
                dados = page['dados']
            except:
                raise Exception('Failed to decode API data')
            yield dados
            page_num += 1

    def getAPISingleRequest(self, param_id, param_page = ''):
        if param_page:
            param_page = '/{}'.format(param_page)
        r = self.http.request(
            'GET',
            '{}{}/{}{}'.format(
                camara_dos_deputados_endpoint,
                self._api_section,
                param_id,
                param_page
            ),
            headers={'accept': 'application/json'}
        )
        if r.status != 200:
            raise Exception('API call failed: {}'.format(param_id))
        try:
            return json.loads(r.data.decode('utf-8'))['dados']
        except:
            raise Exception('Failed to decode API data')

    def getJSONFrom(self, uri, **kwargs):
        r = self.http.request(
            'GET',
            uri,
            fields=kwargs,
            headers={'accept': 'application/json'}
        )
        if r.status != 200:
            raise Exception('API call failed')
        try:
            return json.loads(r.data.decode('utf-8'))
        except:
            raise Exception('Failed to decode API data')

class Deputados(APIData):

    def __init__(self):
        super().__init__('deputados')

    def obterTodosDeputados(self, **kwargs):
        return self.runThroughAllPages(**kwargs)

    def obterDeputado(self, dep_id):
        return self.getAPISingleRequest(dep_id)

class Proposicoes(APIData):

    def __init__(self):
        super().__init__('proposicoes')
    
    def obterTodasProposicoes(self, **kwargs):
        return self.runThroughAllPages(**kwargs)

    def obterProposicao(self, prop_id):
        return self.getAPISingleRequest(prop_id)

    def obterAutoresProposicao(self, prop_id):
        return self.getAPISingleRequest(prop_id, 'autores')

    def obterTramitacoesProposicao(self, prop_id):
        return self.getAPISingleRequest(prop_id, 'tramitacoes')

    def obterVotacoesProposicao(self, prop_id):
        return self.getAPISingleRequest(prop_id, 'votacoes')

class Votacoes(APIData):

    def __init__(self):
        super().__init__('votacoes')

    def obterVotacao(self, vot_id):
        return self.getAPISingleRequest(vot_id)

    def obterVotos(self, vot_id, **kwargs):
        return self.runThroughAllPages(vot_id, 'votos', **kwargs)

class Eventos(APIData):

    def __init__(self):
        super().__init__('eventos')

    def obterTodosEventos(self, **kwargs):
        return self.runThroughAllPages(**kwargs)

    def obterEvento(self, ev_id):
        return self.getAPISingleRequest(ev_id)

    def obterDeputadosEvento(self, ev_id):
        return self.getAPISingleRequest(ev_id, 'deputados')

    def obterPautaEvento(self, ev_id):
        return self.getAPISingleRequest(ev_id, 'pauta')
            

dep = Deputados()
prop = Proposicoes()
vot = Votacoes()
ev = Eventos()

""" IDs de exemplo:
    Deputado: 74171
    Proposição: 2129185
    Votação: 8127, 8122
    Evento: 53848
"""