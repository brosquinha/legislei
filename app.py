# -*- coding: utf-8 -*-
import json
from time import time
from datetime import timedelta, datetime
from SDKs.CamaraDeputados.entidades import Deputados, Eventos, Proposicoes, Votacoes
from flask import Flask, request, render_template


app = Flask(__name__)
dep = Deputados()
ev = Eventos()
prop = Proposicoes()
vot = Votacoes()


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        start_time = time()
        if 'data' in request.form:
            data_inicial = datetime.strptime(request.form['data'], '%Y-%m-%d')
            print(data_inicial)
        else:
            data_inicial = datetime.now()
        deputado = dep.obterDeputado(request.form['deputado'])
        print('Deputado obtido em {0:.5f}'.format(time() - start_time))
        eventos, presenca, todos_eventos = procurarEventosComDeputado(
            deputado['id'], data_inicial)
        print('Eventos obtidos em {0:.5f}'.format(time() - start_time))
        orgaos = obterOrgaosDeputado(deputado['id'], data_inicial)
        print('Orgaos obtidos em {0:.5f}'.format(time() - start_time))
        orgaos_nome = [orgao['nomeOrgao'] for orgao in orgaos]
        eventos_com_deputado = []
        lista_evento_com_deputado = []
        for e in eventos:
            evento = {'evento': e}
            pauta = obterPautaEvento(e['id'])
            if pauta and pauta[1]:
                evento['proposicao'] = pauta[0]
                evento['voto'] = {
                    'voto': obterVotoDeputado(pauta[1][0]['id'], deputado['id']),
                    'pauta': pauta[0]['ementa']
                }
            eventos_com_deputado.append(evento)
        print('Pautas obtidas em {0:.5f}'.format(time() - start_time))
        lista_evento_com_deputado = [eventos_dep['evento']
                                     for eventos_dep in eventos_com_deputado]
        demais_eventos, total_eventos_ausentes = obterEventosAusentes(
            deputado['id'],
            data_inicial,
            lista_evento_com_deputado,
            orgaos_nome,
            todos_eventos
        )
        print('Ausencias obtidas em {0:.5f}'.format(time() - start_time))
        proposicoes_deputado = obterProposicoesDeputado(
            deputado['id'], data_inicial)
        print('Proposicoes obtidas em {0:.5f}'.format(time() - start_time))

        return render_template(
            'consulta_deputado.html',
            deputado_nome=deputado['ultimoStatus']['nome'],
            deputado_partido=deputado['ultimoStatus']['siglaPartido'],
            deputado_uf=deputado['ultimoStatus']['siglaUf'],
            deputado_img=deputado['ultimoStatus']['urlFoto'],
            data_inicial=obterPeriodoDatas(
                data_inicial, weeks=1).strftime("%d/%m/%Y"),
            data_final=data_inicial.strftime("%d/%m/%Y"),
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
    else:
        return render_template('consultar_form.html'), 200


@app.route('/obterDeputados')
def obterDeputados():
    deputados = []
    for page in dep.obterTodosDeputados():
        for item in page:
            deputados.append(item)
    return json.dumps(deputados), 200


def procurarDeputado(nome_deputado):
    for page in dep.obterTodosDeputados():
        for item in page:
            if item['nome'].lower() == nome_deputado.lower():
                return item


def obterPeriodoDatas(data_inicial, **kwargs):
    return data_inicial - timedelta(**kwargs)


def obterDataInicialEFinal(data_inicial):
    last_week = obterPeriodoDatas(data_inicial, weeks=1)
    return ('{}-{:02d}-{:02d}'.format(last_week.year,
                                      last_week.month, last_week.day),
            '{}-{:02d}-{:02d}'.format(data_inicial.year,
                                      data_inicial.month, data_inicial.day))


def obterOrgaosDeputado(deputado_id, data_inicial=datetime.now()):
    orgaos = []
    di = obterDataInicialEFinal(data_inicial)[0]
    for page in dep.obterOrgaosDeputado(deputado_id, dataInicial=di):
        for item in page:
            if (item['dataFim'] == None or
                    datetime.strptime(item['dataFim'], '%Y-%m-%d') > data_inicial):
                orgaos.append(item)
    return orgaos


def procurarEventosComDeputado(deputado_id, data_inicial=datetime.now()):
    eventos_com_deputado = []
    eventos_totais = []
    di, df = obterDataInicialEFinal(data_inicial)
    for page in ev.obterTodosEventos(
        dataInicio=di,
        dataFim=df
    ):
        for item in page:
            eventos_totais.append(item)
            for dep in ev.obterDeputadosEvento(item['id']):
                if dep['id'] == deputado_id:
                    eventos_com_deputado.append(item)
    if len(eventos_totais) == 0:
        presenca = 0
    else:
        presenca = 100*len(eventos_com_deputado)/len(eventos_totais)
    return eventos_com_deputado, presenca, eventos_totais


def obterEventosPrevistosDeputado(deputado_id, data_inicial):
    di, df = obterDataInicialEFinal(data_inicial)
    eventos = []
    for page in dep.obterEventosDeputado(
        deputado_id,
        dataInicio=di,
        dataFim=df
    ):
        for item in page:
            eventos.append(item)
    return eventos


def obterPautaEvento(ev_id):
    pauta = ev.obterPautaEvento(ev_id)
    if not pauta:
        return None
    proposicao_id = pauta[0]['proposicao_']['id']
    if proposicao_id:
        proposicao_detalhes = prop.obterProposicao(proposicao_id)
        votacao = prop.obterVotacoesProposicao(proposicao_id)
        return (proposicao_detalhes, votacao)


def obterVotoDeputado(vot_id, dep_id):
    for page in vot.obterVotos(vot_id):
        for v in page:
            if v['parlamentar']['id'] == dep_id:
                return v['voto']


def obterEventosAusentes(dep_id, data_inicial, eventos_dep, orgaos_dep, todos_eventos):
    demais_eventos = [x for x in todos_eventos if x not in eventos_dep]
    eventos_previstos = obterEventosPrevistosDeputado(dep_id, data_inicial)
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


def obterProposicoesDeputado(dep_id, data_inicial):
    di, df = obterDataInicialEFinal(data_inicial)
    props = []
    for page in prop.obterTodasProposicoes(
        idAutor=dep_id,
        dataApresentacaoInicio=di,
        dataApresentacaoFim=df
    ):
        for item in page:
            props.append(prop.obterProposicao(item['id']))
    return props


def obterTramitacoesDeputado(dep_id, data_inicial):
    di, df = obterDataInicialEFinal(data_inicial)
    props = []
    for page in prop.obterTodasProposicoes(
        idAutor=dep_id,
        dataInicio=di,
        dataFim=df
    ):
        for item in page:
            props.append(item)
    return props


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
