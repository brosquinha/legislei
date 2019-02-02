import json
from datetime import datetime
from time import time

from legislei.exceptions import ModelError
from legislei.houses.casa_legislativa import CasaLegislativa
from legislei.models.relatorio import (Evento, Orgao, Parlamentar, Proposicao,
                                       Relatorio)
from legislei.SDKs.AssembleiaLegislativaSP.comissoes import Comissoes
from legislei.SDKs.AssembleiaLegislativaSP.deputados import Deputados
from legislei.SDKs.AssembleiaLegislativaSP.exceptions import ALESPError
from legislei.SDKs.AssembleiaLegislativaSP.proposicoes import Proposicoes


class ALESPHandler(CasaLegislativa):

    def __init__(self):
        super().__init__()
        self.dep = Deputados()
        self.com = Comissoes()
        self.prop = Proposicoes()
        self.relatorio = Relatorio()

    def obter_relatorio(self, parlamentar_id, data_final=datetime.now(), periodo_dias=7):
        try:
            start_time = time()
            self.relatorio = Relatorio()
            self.relatorio.set_aviso_dados(u'Dados de sessões plenárias não disponível.')
            self.setPeriodoDias(periodo_dias)
            data_final = datetime.strptime(data_final, '%Y-%m-%d')
            data_inicial = self.obterDataInicial(data_final, **self.periodo)
            print('Iniciando...')
            self.obter_parlamentar(parlamentar_id)
            self.relatorio.set_data_inicial(data_inicial)
            self.relatorio.set_data_final(data_final)
            print('Deputado obtido em {0:.5f}'.format(time() - start_time))
            comissoes = self.obterComissoesPorId()
            print('Comissoes por id obtidas em {0:.5f}'.format(time() - start_time))
            votacoes = self.obterVotacoesPorReuniao(parlamentar_id)
            print('Votos do deputado obtidos em {0:.5f}'.format(time() - start_time))
            orgaos_nomes = self.obterComissoesDeputado(
                comissoes, parlamentar_id, data_inicial, data_final)
            print('Comissoes do deputado obtidas em {0:.5f}'.format(time() - start_time))
            self.obterEventosPresentes(
                parlamentar_id, data_inicial, data_final, votacoes, comissoes, orgaos_nomes)
            self.relatorio.set_eventos_ausentes_esperados_total(
                len(self.relatorio.get_eventos_previstos()))
            print('Eventos obtidos em {0:.5f}'.format(time() - start_time))
            self.obterProposicoesDeputado(parlamentar_id, data_inicial, data_final)
            print('Proposicoes obtidas em {0:.5f}'.format(time() - start_time))
            return self.relatorio
        except ALESPError:
            raise ModelError('Erro')
    
    def obter_parlamentar(self, parlamentar_id):
        for deputado in self.dep.obterTodosDeputados():
            if deputado["id"] == parlamentar_id:
                parlamentar = Parlamentar()
                parlamentar.set_cargo('SP')
                parlamentar.set_id(deputado['id'])
                parlamentar.set_nome(deputado['nome'])
                parlamentar.set_partido(deputado['siglaPartido'])
                parlamentar.set_uf('SP')
                parlamentar.set_foto(deputado['urlFoto'])
                self.relatorio.set_parlamentar(parlamentar)
                return parlamentar
    
    def obter_parlamentares(self):
        try:
            return self.dep.obterTodosDeputados()
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
        dep_comissoes_nomes = []
        membros_comissoes = self.com.obterMembrosComissoes()
        for membro in membros_comissoes:
            if ((membro["idDeputado"] == dep_id) and 
                    (membro["dataFim"] == None or 
                    self.obterDatetimeDeStr(membro["dataFim"]) > data_inicial) and
                    self.obterDatetimeDeStr(membro["dataInicio"]) < data_final):
                orgao = Orgao()
                membro["siglaOrgao"] = comissoes[membro["idComissao"]]["sigla"]
                orgao.set_nome(comissoes[membro["idComissao"]]["nome"])
                orgao.set_sigla(membro['siglaOrgao'])
                orgao.set_cargo("Titular" if membro["efetivo"] else "Suplente")
                self.relatorio.add_orgao(orgao)
                dep_comissoes_nomes.append(membro["siglaOrgao"])
        return dep_comissoes_nomes

    def obterEventosPresentes(
            self, dep_id, data_inicial, data_final, reunioes, comissoes, orgaos_nomes):
        eventos_todos = self.com.obterReunioesComissoes()
        presencas = self.com.obterPresencaReunioesComissoes()
        presencas = [x for x in presencas if x["idDeputado"] == dep_id]
        presencas_reunioes_id = [x["idReuniao"] for x in presencas]
        for e in eventos_todos:
            if (self.obterDatetimeDeStr(e["data"]) > data_inicial and
                    self.obterDatetimeDeStr(e["data"]) < data_final):
                evento = Evento()
                evento.set_id(e['id'])
                evento.set_data_inicial(e['data'])
                evento.set_nome(e['convocacao'])
                evento.set_situacao(e['situacao'])
                if e['id'] in reunioes:
                    for r in reunioes[e['id']]:
                        proposicao = Proposicao()
                        proposicao.set_id(r['idDocumento'])
                        proposicao.set_pauta(r['idDocumento'])
                        proposicao.set_url_documento(
                            'https://www.al.sp.gov.br/propositura/?id={}'.format(r['idDocumento']))
                        proposicao.set_voto(r['voto'])
                        proposicao.set_tipo(r['idDocumento'])
                        evento.add_pautas(proposicao)
                orgao = Orgao()
                orgao.set_nome(comissoes[e['idComissao']]['nome'])
                orgao.set_apelido(comissoes[e['idComissao']]['sigla'])
                evento.add_orgaos(orgao)
                if e["id"] in presencas_reunioes_id:
                    evento.set_presente()
                    self.relatorio.add_evento_presente(evento)
                else:
                    evento.set_ausencia_evento_nao_esperado()
                    if (comissoes[e["idComissao"]]["sigla"] in orgaos_nomes and
                        e['situacao'].lower() in ['em preparação', 'em preparacao', 'realizada', 'encerrada']):
                        evento.set_ausente_evento_previsto()
                        self.relatorio.add_evento_previsto(evento)
                    self.relatorio.add_evento_ausente(evento)

    def obterProposicoesDeputado(self, dep_id, data_inicial, data_final):
        proposicoes_deputado = []
        print('Obtendo tipos de documentos...')
        tipos_documentos = self.prop.obterNaturezaDocumentos()
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
                proposicao = Proposicao()
                proposicao.set_id(propositura['id'])
                proposicao.set_url_documento('https://www.al.sp.gov.br/propositura/?id={}'.format(
                    propositura['id']))
                proposicao.set_data_apresentacao(propositura['dataEntrada'])
                proposicao.set_ementa(propositura['ementa'])
                proposicao.set_numero(propositura['numero'])
                if propositura['idNatureza']:
                    for t in tipos_documentos:
                        if t['id'] == propositura['idNatureza']:
                            proposicao.set_tipo(t['sigla'])
                self.relatorio.add_proposicao(proposicao)

    def obterDatetimeDeStr(self, txt):
        #Isso aqui deveria ser responsabilidade da SDK ALESP, não?
        return datetime.strptime(txt[0:19], "%Y-%m-%dT%H:%M:%S")
