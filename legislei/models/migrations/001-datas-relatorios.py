from datetime import datetime

"""
Replaces relatorios' "dataInicial" and "dataFinal" fields' types from
String to Date, and removes unused "idTemp" field.
"""

def success(client):
    relatorios = client.get_default_database()["relatorios"]
    relatorios.update_many({'idTemp': {'$exists': 'true'}}, {
                           '$unset': {'idTemp': ''}})
    for r in relatorios.find({'dataInicial': {'$type': 2}}):
        relatorios.update_one({'_id': r['_id']}, {
                              '$set': {'dataInicial': datetime.strptime(r['dataInicial'], '%d/%m/%Y')}})
    for r in relatorios.find({'dataFinal': {'$type': 2}}):
        relatorios.update_one({'_id': r['_id']}, {
                              '$set': {'dataFinal': datetime.strptime(r['dataFinal'], '%d/%m/%Y')}})


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
