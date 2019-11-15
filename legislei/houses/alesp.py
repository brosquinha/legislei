import json
import logging
from datetime import datetime
from time import time

import pytz

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
        self.brasilia_tz = pytz.timezone('America/Sao_Paulo')

    def obter_relatorio(self, parlamentar_id, data_final=datetime.now(), periodo_dias=7):
        try:
            start_time = time()
            self.relatorio = Relatorio()
            self.relatorio.aviso_dados = u'Dados de sessões plenárias não disponível.'
            self.setPeriodoDias(periodo_dias)
            data_final = datetime.strptime(data_final, '%Y-%m-%d')
            data_inicial = self.obterDataInicial(data_final, **self.periodo)
            logging.info('[ALESP] Parlamentar: {}'.format(parlamentar_id))
            logging.info('[ALESP] Data final: {}'.format(data_final))
            logging.info('[ALESP] Intervalo: {}'.format(periodo_dias))
            self.obter_parlamentar(parlamentar_id)
            self.relatorio.data_inicial = self.brasilia_tz.localize(data_inicial)
            self.relatorio.data_final = self.brasilia_tz.localize(data_final)
            logging.info('[ALESP] Deputado obtido em {0:.5f}s'.format(time() - start_time))
            comissoes = self.obterComissoesPorId()
            logging.info('[ALESP] Comissoes por id obtidas em {0:.5f}s'.format(time() - start_time))
            votacoes = self.obterVotacoesPorReuniao(parlamentar_id)
            logging.info('[ALESP] Votos do deputado obtidos em {0:.5f}s'.format(time() - start_time))
            orgaos_nomes = self.obterComissoesDeputado(
                comissoes, parlamentar_id, data_inicial, data_final)
            logging.info('[ALESP] Comissoes do deputado obtidas em {0:.5f}s'.format(time() - start_time))
            self.obterEventosPresentes(
                parlamentar_id, data_inicial, data_final, votacoes, comissoes, orgaos_nomes)
            self.relatorio.eventos_ausentes_esperados_total = len(self.relatorio.eventos_previstos)
            logging.info('[ALESP] Eventos obtidos em {0:.5f}s'.format(time() - start_time))
            self.obterProposicoesDeputado(parlamentar_id, data_inicial, data_final)
            logging.info('[ALESP] Proposicoes obtidas em {0:.5f}s'.format(time() - start_time))
            logging.info('[ALESP] Relatorio obtido em {0:.5f}s'.format(time() - start_time))
            return self.relatorio
        except ALESPError as e:
            logging.error("[ALESP] {}".format(e))
            raise ModelError('Erro')
    
    def obter_parlamentar(self, parlamentar_id):
        for deputado in self.dep.obterTodosDeputados():
            if deputado["id"] == parlamentar_id:
                parlamentar = Parlamentar()
                parlamentar.cargo = 'SP'
                parlamentar.id = deputado['id']
                parlamentar.nome = deputado['nome']
                parlamentar.partido = deputado['siglaPartido']
                parlamentar.uf = 'SP'
                parlamentar.foto = deputado['urlFoto']
                self.relatorio.parlamentar = parlamentar
                return parlamentar
        return None
    
    def obter_parlamentares(self):
        try:
            parlamentares = []
            for deputado in self.dep.obterTodosDeputados():
                parlamentar = Parlamentar()
                parlamentar.cargo = 'SP'
                parlamentar.id = deputado['id']
                parlamentar.nome = deputado['nome']
                parlamentar.partido = deputado['siglaPartido']
                parlamentar.uf = 'SP'
                parlamentar.foto = deputado['urlFoto'] if 'urlFoto' in deputado else None
                parlamentares.append(parlamentar)
            return parlamentares
        except ALESPError as e:
            logging.error("[ALESP] {}".format(e))
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

    def obterVotoDescritivo(self, codigo_voto):
        codigos = {
            "F": "Favorável",
            "C": "Contrário",
            "S": "Com o voto em separado",
            "P": "Favorável ao projeto",
            "T": "Contrário ao projeto",
            "A": "Abstenção",
            "B": "Branco",
            "O": "Outros"
        }
        return codigos[codigo_voto] if codigo_voto in codigos else codigo_voto

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
                orgao.nome = comissoes[membro["idComissao"]]["nome"]
                orgao.sigla = membro['siglaOrgao']
                orgao.cargo = "Titular" if membro["efetivo"] else "Suplente"
                self.relatorio.orgaos.append(orgao)
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
                evento.id = e['id']
                evento.data_inicial = self.brasilia_tz.localize(
                    self.obterDatetimeDeStr(e["data"]))
                evento.nome = e['convocacao']
                evento.situacao = e['situacao']
                if e['id'] in reunioes:
                    for r in reunioes[e['id']]:
                        proposicao = Proposicao()
                        proposicao.id = r['idDocumento']
                        proposicao.pauta = r['idDocumento']
                        proposicao.url_documento = \
                            'https://www.al.sp.gov.br/propositura/?id={}'.format(r['idDocumento'])
                        proposicao.voto = self.obterVotoDescritivo(r['voto'])
                        proposicao.tipo = r['idDocumento']
                        evento.pautas.append(proposicao)
                orgao = Orgao()
                orgao.nome = comissoes[e['idComissao']]['nome']
                orgao.apelido = comissoes[e['idComissao']]['sigla']
                evento.orgaos.append(orgao)
                if e["id"] in presencas_reunioes_id:
                    evento.set_presente()
                    self.relatorio.eventos_presentes.append(evento)
                else:
                    evento.set_ausencia_evento_nao_esperado()
                    if (comissoes[e["idComissao"]]["sigla"] in orgaos_nomes and
                        e['situacao'].lower() in ['em preparação', 'em preparacao', 'realizada', 'encerrada']):
                        evento.set_ausente_evento_previsto()
                        self.relatorio.eventos_previstos.append(evento)
                    self.relatorio.eventos_ausentes.append(evento)

    def obterProposicoesDeputado(self, dep_id, data_inicial, data_final):
        proposicoes_deputado = []
        logging.debug('[ALESP] Obtendo tipos de documentos...')
        tipos_documentos = self.prop.obterNaturezaDocumentos()
        logging.debug('[ALESP] Obtendo autores...')
        for autor in self.prop.obterTodosAutoresProposicoes():
            if str(autor['idAutor']) == str(dep_id):
                proposicoes_deputado.append(autor['idDocumento'])
        logging.debug('[ALESP] {} proposições obtidas'.format(len(proposicoes_deputado)))
        logging.debug('[ALESP] Obtendo proposicoes...')
        for propositura in self.prop.obterTodasProposicoes():
            if not(propositura['dataEntrada']):
                continue
            data_prop = self.obterDatetimeDeStr(propositura['dataEntrada'])
            if (data_prop > data_inicial and data_prop < data_final and
                    propositura['id'] in proposicoes_deputado):
                proposicao = Proposicao()
                proposicao.id = propositura['id']
                proposicao.url_documento = 'https://www.al.sp.gov.br/propositura/?id={}'.format(
                    propositura['id'])
                proposicao.data_apresentacao = self.brasilia_tz.localize(data_prop)
                proposicao.ementa = propositura['ementa']
                proposicao.numero = propositura['numero']
                if propositura['idNatureza']:
                    for t in tipos_documentos:
                        if t['id'] == propositura['idNatureza']:
                            proposicao.tipo = t['sigla']
                self.relatorio.proposicoes.append(proposicao)

    def obterDatetimeDeStr(self, txt):
        return datetime.strptime(txt[0:19], "%Y-%m-%dT%H:%M:%S")
