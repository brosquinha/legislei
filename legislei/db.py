from mongoengine import connect

def db_connect(db_name, **kwargs):
    """ Connects to MongoDB database """

    if kwargs['db_uri']:
        connect(
            db_name,
            host=kwargs['db_uri']
        )
    else:
        connect(
            db_name,
            host=kwargs['db_host'],
            port=int(kwargs['db_port'])
        )
