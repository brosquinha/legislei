from datetime import datetime

from bson.codec_options import CodecOptions
try:
    import pytz
except ModuleNotFoundError:
    import pip
    if hasattr(pip, 'main'):
        pip.main(['install', 'pytz'])
    else:
        pip._internal.main(['install', 'pytz'])
    import pytz


"""
Changes "dataInicial" and "dataFinal" of Evento types and "dataApresentacao"
of Proposicao type from String to Date
"""

def success(client):
    relatorios = client.get_default_database()['relatorios']
    for relatorio in relatorios.find():
        for tipo_evento in ['eventosAusentes', 'eventosPresentes', 'eventosPrevistos', 'proposicoes']:
            for evento in relatorio[tipo_evento]:
                for nome_data in ['dataInicial', 'dataFinal', 'dataApresentacao']:
                    if not(nome_data in evento and isinstance(evento[nome_data], str)):
                        continue
                    if '-03:00' in evento[nome_data]:
                        evento[nome_data] = evento[nome_data].replace("-03:00", '')
                    if '-02:00' in evento[nome_data]:
                        evento[nome_data] = evento[nome_data].replace("-02:00", '')
                    try:
                        data = datetime.strptime(evento[nome_data], '%Y-%m-%dT%H:%M')
                    except ValueError:
                        try:
                            data = datetime.strptime(evento[nome_data], '%d/%m/%Y')
                        except ValueError:
                            data = datetime.strptime(evento[nome_data], '%Y-%m-%dT%H:%M:%S')
                    brasilia_tz = pytz.timezone('America/Sao_Paulo')
                    data = brasilia_tz.localize(data)
                    relatorios.update_one(
                        {
                            '_id': relatorio['_id'],
                            tipo_evento: {'$elemMatch': {'id': evento['id']}}
                        },
                        {'$set': {"{}.$.{}".format(tipo_evento, nome_data): data}}
                    )
def fail(client):
    relatorios = client.get_default_database()['relatorios'].with_options(
        codec_options=CodecOptions(
            tz_aware=True,
            tzinfo=pytz.timezone('America/Sao_Paulo')
        )
    )
    for relatorio in relatorios.find():
        for tipo_evento in ['eventosAusentes', 'eventosPresentes', 'eventosPrevistos', 'proposicoes']:
            for evento in relatorio[tipo_evento]:
                for nome_data in ['dataInicial', 'dataFinal', 'dataApresentacao']:
                    if not(nome_data in evento and isinstance(evento[nome_data], datetime)):
                        continue
                    data = evento[nome_data].strftime('%Y-%m-%dT%H:%M:%S')
                    relatorios.update_one(
                        {
                            '_id': relatorio['_id'],
                            tipo_evento: {'$elemMatch': {'id': evento['id']}}
                        },
                        {'$set': {"{}.$.{}".format(tipo_evento, nome_data): data}}
                    )
