"""
Moves subscriptions into users, removing its original collection, inscricoes
"""

def success(client):
    inscricoes = client.get_default_database()['inscricoes']
    users = client.get_default_database()['users']
    for inscricao in inscricoes.find():
        users.update_one(
            {'email': inscricao['email']},
            {'$set': {'inscricoes': {
                'parlamentares': inscricao['parlamentares'],
                'intervalo': 7
            }}}
        )
    inscricoes.drop()


def fail(client):
    inscricoes = client.get_default_database()['inscricoes']
    users = client.get_default_database()['users']
    for user in users.find():
        if 'inscricoes' not in user:
            continue
        inscricoes.insert_one({
            'email': user['email'],
            'parlamentares': user['inscricoes']['parlamentares'],
            'intervalo': user['inscricoes']['intervalo']
        })
        users.update_one({'email': user['email']}, {'$unset': {'inscricoes': ''}})