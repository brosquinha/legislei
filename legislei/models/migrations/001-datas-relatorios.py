from datetime import datetime

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
Replaces relatorios' "dataInicial" and "dataFinal" fields' types from
String to Date, and removes unused "idTemp" field.
"""


def success(client):
    relatorios = client.get_default_database()["relatorios"]
    relatorios.update_many({'idTemp': {'$exists': 'true'}}, {
                           '$unset': {'idTemp': ''}})
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    for r in relatorios.find({'dataInicial': {'$type': 2}}):
        data_inicial = datetime.strptime(r['dataInicial'], '%d/%m/%Y')
        data_inicial = brasilia_tz.localize(data_inicial)
        relatorios.update_one({'_id': r['_id']}, {
                              '$set': {'dataInicial': data_inicial}})
    for r in relatorios.find({'dataFinal': {'$type': 2}}):
        data_final = datetime.strptime(r['dataFinal'], '%d/%m/%Y')
        data_final = brasilia_tz.localize(data_final)
        relatorios.update_one({'_id': r['_id']}, {
                              '$set': {'dataFinal': data_final}})


def fail(client):
    relatorios = client.get_default_database()["relatorios"]
    for r in relatorios.find():
        relatorios.update_one({'_id': r['_id']}, {'$set': {'idTemp': "{}-{}".format(
            r['parlamentar']['id'], r['dataFinal'].strftime('%Y-%m-%d'))}})
    for r in relatorios.find({'dataInicial': {'$type': 9}}):
        relatorios.update_one({'_id': r['_id']}, {
                              '$set': {'dataInicial': r['dataInicial'].strftime('%d/%m/%Y')}})
    for r in relatorios.find({'dataFinal': {'$type': 9}}):
        relatorios.update_one({'_id': r['_id']}, {
                              '$set': {'dataFinal': r['dataFinal'].strftime('%d/%m/%Y')}})
