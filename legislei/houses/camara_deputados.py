import json
import logging
from datetime import datetime
from time import time

import pytz
from flask import render_template, request

from legislei.exceptions import ModelError
from legislei.houses.casa_legislativa import CasaLegislativa
from legislei.models.relatorio import (Evento, Orgao, Parlamentar, Proposicao,
                                       Relatorio)
from legislei.SDKs.CamaraDeputados.entidades import (Deputados, Eventos,
                                                     Proposicoes, Votacoes)
from legislei.SDKs.CamaraDeputados.exceptions import (
    CamaraDeputadosConnectionError, CamaraDeputadosError)


class CamaraDeputadosHandler(CasaLegislativa):

    def __init__(self):
        super().__init__()
        self.dep = Deputados()
        self.ev = Eventos()
        self.prop = Proposicoes()
        self.vot = Votacoes()
        self.relatorio = Relatorio()
        self.brasilia_tz = pytz.timezone('America/Sao_Paulo')

    def obter_relatorio(self, parlamentar_id, data_final=None, periodo_dias=7):
        try:
            self.relatorio = Relatorio()
            self.relatorio.aviso_dados = u'Dados de votações em comissões não disponíveis.'
            start_time = time()
            if data_final:
                data_final = datetime.strptime(data_final, '%Y-%m-%d')
            else:
                data_final = datetime.now()
            logging.info('[BR1] Parlamentar: {}'.format(parlamentar_id))
            logging.info('[BR1] Data final: {}'.format(data_final))
            logging.info('[BR1] Intervalo: {}'.format(periodo_dias))
            self.setPeriodoDias(periodo_dias)
            deputado_info = self.obter_parlamentar(parlamentar_id)
            self.relatorio.data_inicial = self.brasilia_tz.localize(
                self.obterDataInicial(data_final, **self.periodo))
            self.relatorio.data_final = self.brasilia_tz.localize(data_final)
            logging.info('[BR1] Deputado obtido em {0:.5f}s'.format(time() - start_time))
            (
                eventos,
                _presenca_total,
                todos_eventos
            ) = self.procurarEventosComDeputado(
                deputado_info.id,
                data_final
            )
            logging.info('[BR1] Eventos obtidos em {0:.5f}s'.format(time() - start_time))
            orgaos = self.obterOrgaosDeputado(deputado_info.id, data_final)
            logging.info('[BR1] Orgaos obtidos em {0:.5f}s'.format(time() - start_time))
            orgaos_nomes = [orgao['nomeOrgao'] for orgao in orgaos]
            for e in eventos:
                evento = Evento()
                evento.id = str(e['id'])
                try:
                    evento.data_inicial = self.obterTimezoneBrasilia(
                        self.obterDatetimeDeStr(e['dataHoraInicio']))
                    evento.data_final = self.obterTimezoneBrasilia(
                        self.obterDatetimeDeStr(e['dataHoraFim']))
                except ValueError:
                    pass
                evento.situacao = e['situacao']
                evento.nome = e['descricao']
                evento.url = e['uri']
                evento.set_presente()
                for o in e['orgaos']:
                    orgao = Orgao()
                    orgao.nome = o['nome']
                    orgao.apelido = o['apelido']
                    evento.orgaos.append(orgao)
                pautas = self.obterPautaEvento(e['id'])
                if pautas == [{'error': True}]:
                    evento.pautas.append(None)
                else:
                    for pauta in pautas:
                        proposicao = Proposicao()
                        if pauta['proposicao_detalhes'] == [{'error': True}]:
                            proposicao = None
                        else:
                            proposicao.id = str(pauta['proposicao_detalhes']['id'])
                            proposicao.tipo = pauta['proposicao_detalhes']['siglaTipo']
                            proposicao.url_documento = \
                                pauta['proposicao_detalhes']['urlInteiroTeor']
                            proposicao.url_autores = \
                                pauta['proposicao_detalhes']['uriAutores']
                            proposicao.pauta = pauta['proposicao_detalhes']['ementa']
                            voto, pauta_votacao = self.obterVotoDeputado(
                                deputado_info.id,
                                proposicao={
                                    'tipo': proposicao.tipo,
                                    'numero': pauta['proposicao_detalhes']['numero'],
                                    'ano': pauta['proposicao_detalhes']['ano']
                                },
                                datas_evento={
                                    'data_inicial': self.obterDatetimeDeStr(e['dataHoraInicio']),
                                    'data_final': self.obterDatetimeDeStr(e['dataHoraFim'])
                                }
                            )
                            proposicao.voto = voto if voto else "ERROR"
                            if pauta_votacao:
                                proposicao.pauta = '{} de {}'.format(
                                    pauta_votacao, proposicao.pauta)
                        evento.pautas.append(proposicao)
                self.relatorio.eventos_presentes.append(evento)
            logging.info('[BR1] Pautas obtidas em {0:.5f}s'.format(time() - start_time))
            (
                eventos_ausentes,
                eventos_ausentes_total,
                _eventos_previstos
            ) = self.obterEventosAusentes(
                deputado_info.id,
                data_final,
                eventos,
                orgaos_nomes,
                todos_eventos
            )
            self.relatorio.eventos_ausentes_esperados_total = eventos_ausentes_total
            for e in eventos_ausentes:
                evento = Evento()
                evento.id = str(e['id'])
                if e['controleAusencia'] == 1:
                    evento.set_ausente_evento_previsto()
                elif e['controleAusencia'] == 2:
                    evento.set_ausencia_evento_esperado()
                else:
                    evento.set_ausencia_evento_nao_esperado()
                try:
                    evento.data_inicial = self.obterTimezoneBrasilia(
                        self.obterDatetimeDeStr(e['dataHoraInicio']))
                    evento.data_final = self.obterTimezoneBrasilia(
                        self.obterDatetimeDeStr(e['dataHoraFim']))
                except ValueError:
                    pass
                evento.nome = e['descricao']
                evento.situacao = e['situacao']
                evento.url = e['uri']
                for o in e['orgaos']:
                    orgao = Orgao()
                    orgao.nome = o['nome']
                    orgao.apelido = o['apelido']
                    evento.orgaos.append(orgao)
                self.relatorio.eventos_ausentes.append(evento)
                if evento.presenca > 1:
                    self.relatorio.eventos_previstos.append(evento)
            logging.info('[BR1] Ausencias obtidas em {0:.5f}s'.format(time() - start_time))
            self.obterProposicoesDeputado(deputado_info, data_final)
            logging.info('[BR1] Proposicoes obtidas em {0:.5f}s'.format(time() - start_time))
            logging.info('[BR1] Relatorio obtido em {0:.5f}s'.format(time() - start_time))
            return self.relatorio
        except CamaraDeputadosError as e:
            logging.error("[BR1] {}".format(e))
            raise ModelError("API Câmara dos Deputados indisponível")

    def obterOrgaosDeputado(self, deputado_id, data_final=datetime.now()):
        orgaos = []
        di, df = self.obterDataInicialEFinal(data_final)
        try:
            for page in self.dep.obterOrgaosDeputado(deputado_id, dataInicio=di, dataFim=df):
                for item in page:
                    dataFim = datetime.now()
                    if item['dataFim'] != None:
                        dataFim = self.obterDatetimeDeStr(item['dataFim'])
                    if (item['dataFim'] == None or dataFim > data_final):
                        orgao = Orgao()
                        if 'nomeOrgao' in item:
                            orgao.nome = item['nomeOrgao']
                        if 'siglaOrgao' in item:
                            orgao.sigla = item['siglaOrgao']
                        if 'titulo' in item:
                            orgao.cargo = item['titulo']
                        self.relatorio.orgaos.append(orgao)
                        orgaos.append(item)
            return orgaos
        except CamaraDeputadosError as e:
            logging.error("[BR1] {}".format(e))
            return [{'nomeOrgao': None}]

    def procurarEventosComDeputado(self, deputado_id, data_final=datetime.now()):
        eventos_com_deputado = []
        eventos_totais = []
        di, df = self.obterDataInicialEFinal(data_final)
        for page in self.ev.obterTodosEventos(
            dataInicio=di,
            dataFim=df
        ):
            for item in page:
                eventos_totais.append(item)
                for dep in self.ev.obterDeputadosEvento(item['id']):
                    if str(dep['id']) == deputado_id:
                        eventos_com_deputado.append(item)
        if len(eventos_totais) == 0:
            presenca = 0
        else:
            presenca = 100*len(eventos_com_deputado)/len(eventos_totais)
        return eventos_com_deputado, presenca, eventos_totais

    def obterEventosPrevistosDeputado(self, deputado_id, data_final):
        di, df = self.obterDataInicialEFinal(data_final)
        eventos = []
        try:
            for page in self.dep.obterEventosDeputado(
                deputado_id,
                dataInicio=di,
                dataFim=df
            ):
                for item in page:
                    eventos.append(item)
            return eventos
        except CamaraDeputadosError as e:
            logging.error("[BR1] {}".format(e))
            return [{'id': None}]

    def obterPautaEvento(self, ev_id):
        try:
            pautas = self.ev.obterPautaEvento(ev_id)
            if not pautas:
                return []
            pautas_unicas = []
            pautas_unicas_ids = []
            for p in pautas:
                proposicao_id = p['proposicao_']['id']
                if proposicao_id not in pautas_unicas_ids and proposicao_id != None:
                    pautas_unicas_ids.append(proposicao_id)
                    pautas_unicas.append(p)
                    try:
                        p['proposicao_detalhes'] = self.prop.obterProposicao(
                            proposicao_id)
                    except CamaraDeputadosError as e:
                        logging.warning("[BR1] {}".format(e))
                        p['proposicao_detalhes'] = [{'error': True}]
            return pautas_unicas
        except CamaraDeputadosError as e:
            logging.error("[BR1] {}".format(e))
            return [{'error': True}]

    def obterVotoDeputado(self, dep_id, proposicao, datas_evento):
        try:
            votos = []
            pautas = []
            for votacao in self.prop.obterVotacoesProposicao(
                tipo=proposicao['tipo'],
                numero=proposicao['numero'],
                ano=proposicao['ano']
            ):
                data_votacao = datetime.strptime(
                    "{} {}".format(votacao["data"], votacao["hora"]),
                    "%d/%m/%Y %H:%M"
                )
                if (data_votacao >= datas_evento['data_inicial'] and
                        data_votacao <= datas_evento['data_final']):
                    pautas.append(votacao['resumo'])
                    for voto in votacao['votos']:
                        if voto['id'] == dep_id:
                            votos.append(voto['voto'])
            if votos == [] and pautas != []:
                return 'Não votou', ','.join(pautas)
            return ','.join(votos), ','.join(pautas)
        except (CamaraDeputadosError, ValueError) as e:
            logging.debug(e)
            return None, None

    def obterEventosAusentes(
            self,
            dep_id,
            data_final,
            eventos_dep,
            orgaos_dep,
            todos_eventos
    ):
        demais_eventos = [x for x in todos_eventos if x not in eventos_dep]
        eventos_previstos = self.obterEventosPrevistosDeputado(
            dep_id, data_final)
        if eventos_previstos:
            eventos_previstos = [x['id'] for x in eventos_previstos]
        else:
            eventos_previstos = []
        ausencia = 0
        for e in demais_eventos:
            if (e['id'] in eventos_previstos):
                ausencia += 1
                e['controleAusencia'] = 1
            elif (e['orgaos'][0]['nome'] in orgaos_dep or
                    e['orgaos'][0]['apelido'] == 'PLEN'):
                ausencia += 1
                e['controleAusencia'] = 2
            else:
                e['controleAusencia'] = None
        return demais_eventos, ausencia, eventos_previstos

    def obterProposicoesDeputado(self, deputado, data_final):
        di, df = self.obterDataInicialEFinal(data_final)
        try:
            for page in self.prop.obterTodasProposicoes(
                idDeputadoAutor=deputado.id,
                dataApresentacaoInicio=di,
                dataApresentacaoFim=df
            ):
                for item in page:
                    if (deputado.nome.lower() in 
                            [x['nome'].lower() for x in self.prop.obterAutoresProposicao(item['id'])]):
                        proposicao = Proposicao()
                        proposicao.id = str(item['id'])
                        p = self.prop.obterProposicao(item['id'])
                        if 'dataApresentacao' in p:
                            try:
                                proposicao.data_apresentacao = self.obterTimezoneBrasilia(
                                    self.obterDatetimeDeStr(p['dataApresentacao']))
                            except ValueError:
                                pass
                        if 'ementa' in p:
                            proposicao.ementa = p['ementa']
                        if 'numero' in p:
                            proposicao.numero = str(p['numero'])
                        if 'siglaTipo' in p:
                            proposicao.tipo = p['siglaTipo']
                        if 'urlInteiroTeor' in p:
                            proposicao.url_documento = p['urlInteiroTeor']
                        self.relatorio.proposicoes.append(proposicao)
        except CamaraDeputadosError as e:
            logging.error("[BR1] {}".format(e))
            self.relatorio.aviso_dados = 'Não foi possível obter proposições do parlamentar.'

    def obterDatetimeDeStr(self, txt):
        if txt == None:
            return txt
        try:
            # Um belo dia a API retornou Epoch ao invés do formato documentado (YYYY-MM-DD), então...
            data = datetime.fromtimestamp(txt/1000)
        except TypeError:
            try:
                data = datetime.strptime(txt, '%Y-%m-%d')
            except ValueError:
                #Agora aparentemente ele volta nesse formato aqui... aiai
                data = datetime.strptime(txt, '%Y-%m-%dT%H:%M')
        return data

    def obterTimezoneBrasilia(self, date):
        if date == None:
            return None
        return self.brasilia_tz.localize(date)

    def obter_parlamentares(self):
        deputados = []
        for page in self.dep.obterTodosDeputados():
            for item in page:
                parlamentar = Parlamentar()
                parlamentar.id = str(item['id'])
                parlamentar.nome = item['nome']
                parlamentar.partido = item['siglaPartido']
                parlamentar.uf = item['siglaUf']
                parlamentar.foto = item['urlFoto']
                deputados.append(parlamentar)
        return deputados

    def obter_parlamentar(self, parlamentar_id):
        try:
            deputado_info = self.dep.obterDeputado(parlamentar_id)
        except CamaraDeputadosConnectionError:
            return None
        parlamentar = Parlamentar()
        parlamentar.cargo = 'BR1'
        parlamentar.id = str(deputado_info['id'])
        parlamentar.nome = deputado_info['ultimoStatus']['nome']
        parlamentar.partido = deputado_info['ultimoStatus']['siglaPartido']
        parlamentar.uf = deputado_info['ultimoStatus']['siglaUf']
        parlamentar.foto = deputado_info['ultimoStatus']['urlFoto']
        self.relatorio.parlamentar = parlamentar
        return parlamentar
