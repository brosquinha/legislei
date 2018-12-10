import json
from datetime import datetime
from time import time
from SDKs.AssembleiaLegislativaSP.deputados import Deputados
from SDKs.AssembleiaLegislativaSP.comissoes import Comissoes
from SDKs.AssembleiaLegislativaSP.proposicoes import Proposicoes
from SDKs.AssembleiaLegislativaSP.exceptions import ALESPError
from models.parlamentares import ParlamentaresApp
from exceptions import ModelError

class DeputadosALESPApp(ParlamentaresApp):

    def __init__(self):
        super().__init__()
        self.dep = Deputados()
        self.com = Comissoes()
        self.prop = Proposicoes()

    def consultar_deputado(self, dep_id, data_final=datetime.now(), periodo=7):
        try:
            start_time = time()
            relatorio = {}
            data_final = datetime.strptime(data_final, '%Y-%m-%d')
            data_inicial = self.obterDataInicial(data_final, **self.periodo)
            relatorio['mensagem'] = u'Dados de sessões plenárias não disponível.'
            print('Iniciando...')
            relatorio["deputado"] = {"ultimoStatus": self.obterDeputado(dep_id)}
            relatorio["deputado"]["ultimoStatus"]["siglaUf"] = 'SP'
            relatorio["dataInicial"] = data_inicial.strftime("%d/%m/%Y")
            relatorio['dataFinal'] = data_final.strftime("%d/%m/%Y")
            print('Deputado obtido em {0:.5f}'.format(time() - start_time))
            comissoes = self.obterComissoesPorId()
            print('Comissoes por id obtidas em {0:.5f}'.format(time() - start_time))
            votacoes = self.obterVotacoesPorReuniao(dep_id)
            print('Votos do deputado obtidos em {0:.5f}'.format(time() - start_time))
            relatorio['orgaos'], orgaos_nomes = self.obterComissoesDeputado(
                comissoes, dep_id, data_inicial, data_final)
            print('Comissoes do deputado obtidas em {0:.5f}'.format(time() - start_time))
            eventos_presentes, eventos_ausentes = self.obterEventosPresentes(
                dep_id, data_inicial, data_final)
            relatorio['eventosPresentes'] = []
            for evento in eventos_presentes:
                pautas = []
                if evento['id'] in votacoes:
                    for votacao in votacoes[evento['id']]:
                        pautas.append({
                            'voto': {
                                'voto': votacao['voto'],
                                'pauta': votacao['idDocumento']
                            },
                            'proposicao': {
                                'siglaTipo': votacao['idDocumento'],
                                'urlInteiroTeor': 'https://www.al.sp.gov.br/propositura/?id={}'.format(votacao['idDocumento'])
                            }
                        })
                relatorio['eventosPresentes'].append({
                    "evento": {
                        'titulo': evento['convocacao'],
                        'dataHoraInicio': evento['data'],
                        'dataHoraFim': None,
                        'descricaoSituacao': evento['situacao'],
                        'orgaos': [{
                            'nome': comissoes[evento["idComissao"]]["nome"],
                            'apelido': comissoes[evento["idComissao"]]["sigla"]
                        }],
                    },
                    'pautas': pautas
                })
            relatorio['eventosAusentes'] = []
            relatorio['eventosPrevistos'] = []
            for evento in eventos_ausentes:
                evento_dict = {
                    'titulo': evento['convocacao'],
                    'dataHoraInicio': evento['data'],
                    'dataHoraFim': None,
                    'descricaoSituacao': evento['situacao'],
                    'orgaos': [{
                        'nome': comissoes[evento["idComissao"]]["nome"],
                        'apelido': comissoes[evento["idComissao"]]["sigla"]
                    }]
                }
                if (comissoes[evento["idComissao"]]["sigla"] in orgaos_nomes and
                        evento['situacao'].lower() in ['em preparação', 'em preparacao', 'realizada', 'encerrada']):
                    evento_dict['controleAusencia'] = 2
                    relatorio['eventosPrevistos'].append(evento_dict)
                relatorio['eventosAusentes'].append(evento_dict)
            relatorio['eventosAusentesTotal'] = len(relatorio['eventosPrevistos'])
            print('Eventos obtidos em {0:.5f}'.format(time() - start_time))
            relatorio['proposicoes'] = self.obterProposicoesDeputado(dep_id, data_inicial, data_final)
            print('Proposicoes obtidas em {0:.5f}'.format(time() - start_time))
            return relatorio
        except ALESPError:
            raise ModelError('Erro')
    
    def obterDeputado(self, dep_id):
        for deputado in self.dep.obterTodosDeputados():
            if deputado["id"] == dep_id:
                return deputado
    
    def obterDeputados(self):
        try:
            return json.dumps(self.dep.obterTodosDeputados()), 200
        except ALESPError:
            raise ModelError("Erro da API da ALESP")

    def obterComissoesPorId(self):
        resultado = {}
        comissoes = self.com.obterComissoes()
        for comissao in comissoes:
            resultado[comissao["id"]] = comissao
        return resultado

    def obterVotacoesPorReuniao(self, dep_id):
        resultado = {}
        votacoes = self.com.obterVotacoesComissoes()
        for votacao in votacoes:
            if votacao['idDeputado'] != dep_id:
                continue
            if votacao['idReuniao'] not in resultado:
                resultado[votacao["idReuniao"]] = []
            resultado[votacao["idReuniao"]].append(votacao)
        return resultado

    def obterComissoesDeputado(self, comissoes, dep_id, data_inicial, data_final):
        dep_comissoes = []
        dep_comissoes_nomes = []
        membros_comissoes = self.com.obterMembrosComissoes()
        for membro in membros_comissoes:
            if ((membro["idDeputado"] == dep_id) and 
                    (membro["dataFim"] == None or 
                    self.obterDatetimeDeStr(membro["dataFim"]) > data_final) and
                    self.obterDatetimeDeStr(membro["dataInicio"]) < data_final):
                membro["nomeComissao"] = comissoes[membro["idComissao"]]["nome"]
                membro["siglaOrgao"] = comissoes[membro["idComissao"]]["sigla"]
                membro["nomePapel"] = "Titular" if membro["efetivo"] else "Suplente"
                membro["nomeOrgao"] = membro["nomeComissao"]
                dep_comissoes_nomes.append(membro["siglaOrgao"])
                dep_comissoes.append(membro)
        return dep_comissoes, dep_comissoes_nomes

    def obterEventosPresentes(self, dep_id, data_inicial, data_final):
        eventos_todos = self.com.obterReunioesComissoes()
        presencas = self.com.obterPresencaReunioesComissoes()
        eventos_ausentes = []
        eventos_presentes = []
        presencas = [x for x in presencas if x["idDeputado"] == dep_id]
        presencas_reunioes_id = [x["idReuniao"] for x in presencas]
        for evento in eventos_todos:
            if (self.obterDatetimeDeStr(evento["data"]) > data_inicial and
                    self.obterDatetimeDeStr(evento["data"]) < data_final):
                if evento["id"] in presencas_reunioes_id:
                    eventos_presentes.append(evento)
                else:
                    eventos_ausentes.append(evento)
        return eventos_presentes, eventos_ausentes

    def obterProposicoesDeputado(self, dep_id, data_inicial, data_final):
        proposicoes = []
        proposicoes_deputado = []
        print('Obtendo autores...')
        for autor in self.prop.obterTodosAutoresProposicoes():
            if autor['idAutor'] == dep_id:
                proposicoes_deputado.append(autor['idDocumento'])
        print(len(proposicoes_deputado))
        print('Obtendo proposicoes...')
        for propositura in self.prop.obterTodasProposicoes():
            if not(propositura['dataEntrada']):
                continue
            data_prop = self.obterDatetimeDeStr(propositura['dataEntrada'])
            if (data_prop > data_inicial and data_prop < data_final and
                    propositura['id'] in proposicoes_deputado):
                propositura['urlInteiroTeor'] = 'https://www.al.sp.gov.br/propositura/?id={}'.format(
                    propositura['id'])
                propositura['dataApresentacao'] = propositura['dataEntrada']
                proposicoes.append(propositura)
        return proposicoes

    def obterDatetimeDeStr(self, txt):
        #Isso aqui deveria ser responsabilidade da SDK ALESP, não?
        return datetime.strptime(txt[0:19], "%Y-%m-%dT%H:%M:%S")
