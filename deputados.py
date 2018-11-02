import json
from time import time
from datetime import datetime
from flask import render_template, request
from SDKs.CamaraDeputados.entidades import Deputados, Eventos, Proposicoes, Votacoes
from SDKs.CamaraDeputados.exceptions import CamaraDeputadosError
from parlamentares import ParlamentaresApp

class DeputadosApp(ParlamentaresApp):

    def __init__(self):
        self.dep = Deputados()
        self.ev = Eventos()
        self.prop = Proposicoes()
        self.vot = Votacoes()
        self.periodo = {'weeks': 1}

    def consultar_deputado(self):
        try:
            start_time = time()
            if 'data' in request.form:
                data_final = datetime.strptime(request.form['data'], '%Y-%m-%d')
                print(data_final)
            else:
                data_final = datetime.now()
            deputado = self.dep.obterDeputado(request.form['deputado'])
            print('Deputado obtido em {0:.5f}'.format(time() - start_time))
            eventos, presenca, todos_eventos = self.procurarEventosComDeputado(
                deputado['id'], data_final)
            print('Eventos obtidos em {0:.5f}'.format(time() - start_time))
            orgaos = self.obterOrgaosDeputado(deputado['id'], data_final)
            print('Orgaos obtidos em {0:.5f}'.format(time() - start_time))
            orgaos_nome = [orgao['nomeOrgao'] for orgao in orgaos]
            eventos_com_deputado = []
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
                                        pauta['votacao'][0]['id'], deputado['id']),
                                    'pauta': pauta['proposicao_detalhes']['ementa']
                                }
                            evento['pautas'].append(
                                {'proposicao': proposicao, 'voto': voto}
                            )
                eventos_com_deputado.append(evento)
            print('Pautas obtidas em {0:.5f}'.format(time() - start_time))
            lista_evento_com_deputado = [eventos_dep['evento']
                                            for eventos_dep in eventos_com_deputado]
            demais_eventos, total_eventos_ausentes, eventos_previstos = self.obterEventosAusentes(
                deputado['id'],
                data_final,
                lista_evento_com_deputado,
                orgaos_nome,
                todos_eventos
            )
            print('Ausencias obtidas em {0:.5f}'.format(time() - start_time))
            proposicoes_deputado = self.obterProposicoesDeputado(
                deputado['id'], data_final)
            print('Proposicoes obtidas em {0:.5f}'.format(time() - start_time))

            return render_template(
                'consulta_deputado.html',
                deputado_nome=deputado['ultimoStatus']['nome'],
                deputado_partido=deputado['ultimoStatus']['siglaPartido'],
                deputado_uf=deputado['ultimoStatus']['siglaUf'],
                deputado_img=deputado['ultimoStatus']['urlFoto'],
                data_inicial=self.obterDataInicial(
                    data_final, **self.periodo).strftime("%d/%m/%Y"),
                data_final=data_final.strftime("%d/%m/%Y"),
                presenca='{0:.2f}%'.format(presenca),
                presenca_relativa='{0:.2f}%'.format(
                    100*len(eventos)/(total_eventos_ausentes+len(eventos))),
                total_eventos_ausentes=total_eventos_ausentes,
                orgaos=orgaos,
                orgaos_nome=orgaos_nome,
                eventos=eventos_com_deputado,
                eventos_eventos=lista_evento_com_deputado,
                todos_eventos=demais_eventos,
                eventos_previstos=eventos_previstos,
                proposicoes_deputado=proposicoes_deputado,
            ), 200
        except CamaraDeputadosError:
            return render_template(
                'erro.html',
                erro_titulo='500 - Serviço indisponível',
                erro_descricao='Serviço da Câmara dos Deputados está indisponível. :('
            ), 500
        except KeyError:
            return render_template(
                'erro.html',
                erro_titulo='400 - Preencha o formulário',
                erro_descricao='Aeow, preencha o formulário, sim?'
            ), 400

    def obterOrgaosDeputado(self, deputado_id, data_final=datetime.now()):
        orgaos = []
        di = self.formatarDatasYMD(
            self.obterDataInicial(data_final, **self.periodo)
        )
        try:
            for page in self.dep.obterOrgaosDeputado(deputado_id, dataInicial=di):
                for item in page:
                    try:
                        #Um belo dia a API retornou Epoch ao invés do formato documentado (YYYY-MM-DD), então...
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
                        p['proposicao_detalhes'] = self.prop.obterProposicao(proposicao_id)
                    except CamaraDeputadosError:
                        p['proposicao_detalhes'] = [{'error': True}]
                    try:
                        p['votacao'] = self.prop.obterVotacoesProposicao(proposicao_id)
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
        eventos_previstos = self.obterEventosPrevistosDeputado(dep_id, data_final)
        eventos_previstos = [x['id'] for x in eventos_previstos]
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