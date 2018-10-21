from .APIData import APIData


class Deputados(APIData):

    def __init__(self):
        super(Deputados, self).__init__('deputados')

    def obterTodosDeputados(self, **kwargs):
        return self.runThroughAllPages(**kwargs)

    def obterDeputado(self, dep_id):
        return self.getAPISingleRequest(dep_id)

    def obterOrgaosDeputado(self, dep_id, **kwargs):
        return self.runThroughAllPages(dep_id, 'orgaos', **kwargs)


class Eventos(APIData):

    def __init__(self):
        super(Eventos, self).__init__('eventos')

    def obterTodosEventos(self, **kwargs):
        return self.runThroughAllPages(**kwargs)

    def obterEvento(self, ev_id):
        return self.getAPISingleRequest(ev_id)

    def obterDeputadosEvento(self, ev_id):
        return self.getAPISingleRequest(ev_id, 'deputados')

    def obterPautaEvento(self, ev_id):
        return self.getAPISingleRequest(ev_id, 'pauta')


class Proposicoes(APIData):

    def __init__(self):
        super(Proposicoes, self).__init__('proposicoes')
    
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
        super(Votacoes, self).__init__('votacoes')

    def obterVotacao(self, vot_id):
        return self.getAPISingleRequest(vot_id)

    def obterVotos(self, vot_id, **kwargs):
        return self.runThroughAllPages(vot_id, 'votos', **kwargs)