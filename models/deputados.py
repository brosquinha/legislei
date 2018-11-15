import json
from time import time
from datetime import datetime
from flask import render_template, request
from SDKs.CamaraDeputados.entidades import Deputados, Eventos, Proposicoes, Votacoes
from SDKs.CamaraDeputados.exceptions import CamaraDeputadosError
from models.parlamentares import ParlamentaresApp
from exceptions import ModelError


class DeputadosApp(ParlamentaresApp):

    def __init__(self):
        super().__init__()
        self.dep = Deputados()
        self.ev = Eventos()
        self.prop = Proposicoes()
        self.vot = Votacoes()

    def consultar_deputado(self, deputado_id, data_final=None, periodo_dias=7):
        try:
            relatorio_deputado = {}
            start_time = time()
            if data_final:
                data_final = datetime.strptime(data_final, '%Y-%m-%d')
                print(data_final)
            else:
                data_final = datetime.now()
            try:
                if int(periodo_dias) in range(7, 29):
                    self.periodo['days'] = int(periodo_dias)
            except ValueError:
                periodo_dias = 7
            relatorio_deputado['deputado'] = self.dep.obterDeputado(deputado_id)
            relatorio_deputado['dataInicial'] = self.obterDataInicial(
                data_final, **self.periodo).strftime("%d/%m/%Y")
            relatorio_deputado['dataFinal'] = data_final.strftime("%d/%m/%Y")
            print('Deputado obtido em {0:.5f}'.format(time() - start_time))
            (
                eventos,
                relatorio_deputado['presencaTotal'],
                todos_eventos
            ) = self.procurarEventosComDeputado(
                relatorio_deputado['deputado']['id'],
                data_final
            )
            print('Eventos obtidos em {0:.5f}'.format(time() - start_time))
            relatorio_deputado['orgaos'] = self.obterOrgaosDeputado(
                relatorio_deputado['deputado']['id'], data_final)
            print('Orgaos obtidos em {0:.5f}'.format(time() - start_time))
            relatorio_deputado['orgaosNomes'] = [orgao['nomeOrgao']
                                                for orgao in relatorio_deputado['orgaos']]
            relatorio_deputado['eventosPresentes'] = []
            lista_evento_com_deputado = []
            for e in eventos:
                evento = {
                    'evento': e,
                    'pautas': []
                }
                pautas = self.obterPautaEvento(e['id'])
                if pautas == [{'error': True}]:
                    evento['pautas'] = {'error': True}
                else:
                    for pauta in pautas:
                        if len(pauta['votacao']):
                            if pauta['proposicao_detalhes'] == [{'error': True}]:
                                proposicao = {'error': True}
                            else:
                                proposicao = pauta['proposicao_detalhes']
                            if pauta['votacao'] == [{'error': True}]:
                                voto = {'error': True}
                            else:
                                voto = {
                                    'voto': self.obterVotoDeputado(
                                        pauta['votacao'][0]['id'], relatorio_deputado['deputado']['id']),
                                    'pauta': pauta['proposicao_detalhes']['ementa']
                                }
                            evento['pautas'].append(
                                {'proposicao': proposicao, 'voto': voto}
                            )
                relatorio_deputado['eventosPresentes'].append(evento)
            print('Pautas obtidas em {0:.5f}'.format(time() - start_time))
            lista_evento_com_deputado = [eventos_dep['evento']
                                        for eventos_dep in relatorio_deputado['eventosPresentes']]
            (
                relatorio_deputado['eventosAusentes'],
                relatorio_deputado['eventosAusentesTotal'],
                relatorio_deputado['eventosPrevistos']
            ) = self.obterEventosAusentes(
                relatorio_deputado['deputado']['id'],
                data_final,
                lista_evento_com_deputado,
                relatorio_deputado['orgaosNomes'],
                todos_eventos
            )
            print('Ausencias obtidas em {0:.5f}'.format(time() - start_time))
            relatorio_deputado['presencaRelativa'] = '{0:.2f}%'.format(
                100*len(eventos)/(relatorio_deputado['eventosAusentesTotal']+len(eventos)))
            relatorio_deputado['presencaTotal'] = '{0:.2f}%'.format(
                relatorio_deputado['presencaTotal'])
            relatorio_deputado['proposicoes'] = self.obterProposicoesDeputado(
                relatorio_deputado['deputado']['id'], data_final)
            print('Proposicoes obtidas em {0:.5f}'.format(time() - start_time))
            
            return relatorio_deputado
        except CamaraDeputadosError:
            raise ModelError("API Câmara dos Deputados indisponível")

    def obterOrgaosDeputado(self, deputado_id, data_final=datetime.now()):
        orgaos = []
        di = self.formatarDatasYMD(
            self.obterDataInicial(data_final, **self.periodo)
        )
        try:
            for page in self.dep.obterOrgaosDeputado(deputado_id, dataInicial=di):
                for item in page:
                    try:
                        # Um belo dia a API retornou Epoch ao invés do formato documentado (YYYY-MM-DD), então...
                        if (item['dataFim'] == None or
                                datetime.fromtimestamp(item['dataFim']/1000) > data_final):
                            orgaos.append(item)
                    except TypeError:
                        if (item['dataFim'] == None or
                                datetime.strptime(item['dataFim'], '%Y-%m-%d') > data_final):
                            orgaos.append(item)
            return orgaos
        except CamaraDeputadosError:
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
                    if dep['id'] == deputado_id:
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
        except CamaraDeputadosError:
            eventos = [{'id': None}]

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
                    except CamaraDeputadosError:
                        p['proposicao_detalhes'] = [{'error': True}]
                    try:
                        p['votacao'] = self.prop.obterVotacoesProposicao(
                            proposicao_id)
                    except CamaraDeputadosError:
                        p['votacao'] = [{'error': True}]
            return pautas_unicas
        except CamaraDeputadosError:
            return [{'error': True}]

    def obterVotoDeputado(self, vot_id, dep_id):
        try:
            for page in self.vot.obterVotos(vot_id):
                for v in page:
                    if v['parlamentar']['id'] == dep_id:
                        return v['voto']
        except CamaraDeputadosError:
            return False

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

    def obterProposicoesDeputado(self, dep_id, data_final):
        di, df = self.obterDataInicialEFinal(data_final)
        props = []
        try:
            for page in self.prop.obterTodasProposicoes(
                idAutor=dep_id,
                dataApresentacaoInicio=di,
                dataApresentacaoFim=df
            ):
                for item in page:
                    props.append(self.prop.obterProposicao(item['id']))
            return props
        except CamaraDeputadosError:
            return [{'error': True}]

    def obterTramitacoesDeputado(self, dep_id, data_final):
        di, df = self.obterDataInicialEFinal(data_final)
        props = []
        for page in self.prop.obterTodasProposicoes(
            idAutor=dep_id,
            dataInicio=di,
            dataFim=df
        ):
            for item in page:
                props.append(item)
        return props

    def obterDeputados(self):
        deputados = []
        for page in self.dep.obterTodosDeputados():
            for item in page:
                deputados.append(item)
        return json.dumps(deputados), 200
