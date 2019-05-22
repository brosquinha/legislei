"""
Removes reports that use old parlamentar cargo system, since they lack some vital data
and do not follow some necessary conditions
"""

def success(client):
    relatorios = client.get_default_database()["relatorios"]
    relatorios.delete_many({'parlamentar.cargo': 'deputado federal'})
    relatorios.delete_many({'parlamentar.cargo': 'deputado estadual'})
    relatorios.delete_many({'parlamentar.cargo': 'vereador'})

def fail(client):
    pass