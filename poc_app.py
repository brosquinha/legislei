import json
from datetime import timedelta, datetime
from poc_sdk import Deputados, Eventos, Proposicoes, Votacoes
from flask import Flask, request, render_template


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'data' in request.form:
            data_inicial = datetime.strptime(request.form['data'], '%Y-%m-%d')
            print(data_inicial)
        else:
            data_inicial = datetime.now()
        deputado = procurarDeputado(request.form['deputado'])
        eventos, presenca, todos_eventos = procurarEventosComDeputado(
            deputado['id'], data_inicial)
        orgaos = obterOrgaosDeputado(deputado['id'], data_inicial)
        orgaos_nome = [orgao['nomeOrgao'] for orgao in orgaos]
        eventos_com_deputado = []
        lista_evento_com_deputado = []
        for e in eventos:
            evento = {'evento': e}
            pauta = obterPautaEvento(e['id'])
            # print(pauta)
            if pauta and pauta[1]:
                evento['proposicao'] = pauta[0]
                evento['voto'] = {
                    'voto': obterVotoDeputado(pauta[1][0]['id'], deputado['id']),
                    'pauta': pauta[0]['ementa']
                }
            eventos_com_deputado.append(evento)
        lista_evento_com_deputado = [eventos_dep['evento']
                                     for eventos_dep in eventos_com_deputado]
        demais_eventos, total_eventos_ausentes = obterEventosAusentes(
            lista_evento_com_deputado, orgaos_nome, todos_eventos
        )

        return render_template(
            'consulta_deputado.html',
            deputado_nome=deputado['nome'],
            deputado_partido=deputado['siglaPartido'],
            deputado_uf=deputado['siglaUf'],
            deputado_img=deputado['urlFoto'],
            data_inicial=data_inicial.strftime("%d/%m/%Y"),
            presenca='{0:.2f}%'.format(presenca),
            presenca_relativa='{0:.2f}%'.format(100*len(eventos)/total_eventos_ausentes),
            total_eventos_ausentes=total_eventos_ausentes,
            orgaos=orgaos,
            orgaos_nome=orgaos_nome,
            eventos=eventos_com_deputado,
            eventos_eventos=lista_evento_com_deputado,
            todos_eventos=demais_eventos
        ), 200
    else:
        return render_template('consultar_form.html'), 200


@app.route('/obterDeputados')
def obterDeputados():
    dep = Deputados()
    deputados = []
    for page in dep.obterTodosDeputados():
        for item in page:
            deputados.append(item)
    return json.dumps(deputados), 200


def procurarDeputado(nome_deputado):
    dep = Deputados()
    for page in dep.obterTodosDeputados():
        for item in page:
            if item['nome'].lower() == nome_deputado.lower():
                return item


def obterDataInicialEFinal(data_inicial):
    agora = data_inicial
    last_week = agora - timedelta(weeks=1)
    return ('{}-{:02d}-{:02d}'.format(last_week.year,
                                      last_week.month, last_week.day),
            '{}-{:02d}-{:02d}'.format(agora.year,
                                      agora.month, agora.day))


def obterOrgaosDeputado(deputado_id, data_inicial=datetime.now()):
    dep = Deputados()
    orgaos = []
    di, df = obterDataInicialEFinal(data_inicial)
    for page in dep.obterOrgaosDeputado(deputado_id, dataInicial=di):
        for item in page:
            if (item['dataFim'] == None or
                    datetime.strptime(item['dataFim'], '%Y-%m-%d') > data_inicial):
                orgaos.append(item)
    return orgaos


def procurarEventosComDeputado(deputado_id, data_inicial=datetime.now()):
    ev = Eventos()
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
    print('Presença: {0:.2f}%'.format(presenca))
    return eventos_com_deputado, presenca, eventos_totais


def obterPautaEvento(ev_id):
    ev = Eventos()
    prop = Proposicoes()
    pauta = ev.obterPautaEvento(ev_id)
    if not pauta:
        return None
    proposicao_id = pauta[0]['proposicao_']['id']
    if proposicao_id:
        proposicao_detalhes = prop.obterProposicao(proposicao_id)
        votacao = prop.obterVotacoesProposicao(proposicao_id)
        return (proposicao_detalhes, votacao)


def obterVotoDeputado(vot_id, dep_id):
    vot = Votacoes()
    for page in vot.obterVotos(vot_id):
        for v in page:
            if v['parlamentar']['id'] == dep_id:
                return v['voto']


def obterEventosAusentes(eventos_dep, orgaos_dep, todos_eventos):
    demais_eventos = [x for x in todos_eventos if x not in eventos_dep]
    ausencia = 0
    for e in demais_eventos:
        if (e['orgaos'][0]['nome'] in orgaos_dep or 
                e['orgaos'][0]['apelido'] == 'PLEN'):
            ausencia += 1
            e['controleAusencia'] = True
        else:
            e['controleAusencia'] = None
    return demais_eventos, ausencia


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
