from datetime import timedelta, datetime
from poc_sdk import Deputados, Eventos, Proposicoes, Votacoes


def procurarDeputado(nome_deputado):
    dep = Deputados()
    for page in dep.obterTodosDeputados():
        for item in page:
            if item['nome'].lower() == nome_deputado.lower():
                return item


def procurarEventosComDeputado(deputado_id):
    ev = Eventos()
    eventos_com_deputado = []
    eventos_totais = 0
    agora =  datetime.now() #datetime(2018, 6, 26)
    last_week = agora - timedelta(weeks=1)
    for page in ev.obterTodosEventos(
        dataInicio='{}-{:02d}-{:02d}'.format(last_week.year,
                                     last_week.month, last_week.day),
        dataFim='{}-{:02d}-{:02d}'.format(agora.year,
                                  agora.month, agora.day)
    ):
        for item in page:
            for dep in ev.obterDeputadosEvento(item['id']):
                eventos_totais += 1
                if dep['id'] == deputado_id:
                    eventos_com_deputado.append(item)
    print('Presença: {0:.2f}%'.format(100*len(eventos_com_deputado)/eventos_totais))
    return eventos_com_deputado


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


def main(*args, **kwargs):
    resp = input('Inserir nome de Deputado: ')
    deputado = procurarDeputado(resp)
    print(deputado)
    eventos = procurarEventosComDeputado(deputado['id'])
    for e in eventos:
        pauta = obterPautaEvento(e['id'])
        if pauta and pauta[1]:
            print('Votou {} em {}'.format(
                obterVotoDeputado(pauta[1][0]['id'], deputado['id']),
                pauta[0]['ementa']
            ))


if __name__ == '__main__':
    main()
