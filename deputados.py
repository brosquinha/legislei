import json
from time import time
from datetime import datetime
from flask import render_template, request
from SDKs.CamaraDeputados.entidades import Deputados, Eventos, Proposicoes, Votacoes
from parlamentares import ParlamentaresApp

class DeputadosApp(ParlamentaresApp):

    def __init__(self):
        self.dep = Deputados()
        self.ev = Eventos()
        self.prop = Proposicoes()
        self.vot = Votacoes()

    def consultar_deputado(self):
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
            evento = {'evento': e}
            pauta = self.obterPautaEvento(e['id'])
            if pauta and pauta[1]:
                evento['proposicao'] = pauta[0]
                evento['voto'] = {
                    'voto': self.obterVotoDeputado(pauta[1][0]['id'], deputado['id']),
                    'pauta': pauta[0]['ementa']
                }
            eventos_com_deputado.append(evento)
        print('Pautas obtidas em {0:.5f}'.format(time() - start_time))
        lista_evento_com_deputado = [eventos_dep['evento']
                                        for eventos_dep in eventos_com_deputado]
        demais_eventos, total_eventos_ausentes = self.obterEventosAusentes(
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
                data_final, weeks=1).strftime("%d/%m/%Y"),
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
            proposicoes_deputado=proposicoes_deputado,
        ), 200

    def obterOrgaosDeputado(self, deputado_id, data_final=datetime.now()):
        orgaos = []
        di = self.formatarDatasYMD(
            self.obterDataInicial(data_final, weeks=1)
        )
        for page in self.dep.obterOrgaosDeputado(deputado_id, dataInicial=di):
            for item in page:
                if (item['dataFim'] == None or
                        datetime.strptime(item['dataFim'], '%Y-%m-%d') > data_final):
                    orgaos.append(item)
        return orgaos


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
        for page in self.dep.obterEventosDeputado(
            deputado_id,
            dataInicio=di,
            dataFim=df
        ):
            for item in page:
                eventos.append(item)
        return eventos


    def obterPautaEvento(self, ev_id):
        pauta = self.ev.obterPautaEvento(ev_id)
        if not pauta:
            return None
        proposicao_id = pauta[0]['proposicao_']['id']
        if proposicao_id:
            proposicao_detalhes = self.prop.obterProposicao(proposicao_id)
            votacao = self.prop.obterVotacoesProposicao(proposicao_id)
            return (proposicao_detalhes, votacao)


    def obterVotoDeputado(self, vot_id, dep_id):
        for page in self.vot.obterVotos(vot_id):
            for v in page:
                if v['parlamentar']['id'] == dep_id:
                    return v['voto']


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
        return demais_eventos, ausencia


    def obterProposicoesDeputado(self, dep_id, data_final):
        di, df = self.obterDataInicialEFinal(data_final)
        props = []
        for page in self.prop.obterTodasProposicoes(
            idAutor=dep_id,
            dataApresentacaoInicio=di,
            dataApresentacaoFim=df
        ):
            for item in page:
                props.append(self.prop.obterProposicao(item['id']))
        return props


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