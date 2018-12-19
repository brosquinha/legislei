import os
import settings
import pymongo

class MongoDBClient():
    """
    Cliente para conexão com o MongoDB
    """

    def __init__(self):
        if os.environ.get("MONGODB_URI"):
            self._mongo_client = pymongo.MongoClient(os.environ.get("MONGODB_URI"))
        else:
            self._mongo_client = pymongo.MongoClient(
                host=os.environ.get("MONGODB_HOST", "localhost"),
                port=int(os.environ.get("MONGODB_PORT", 27017))
            )
        self._mongo_db = self._mongo_client.get_database(os.environ.get("MONGODB_DBNAME"))

    def get_db(self):
        return self._mongo_db

    def get_collection(self, col_name):
        """
        Obtém a coleção `col_name` do banco de dados padrão

        :param col_name: Nome de coleção
        :type col_name: String

        :return: Coleção MongoDB
        :rtype: Collection
        """
        return self._mongo_db[col_name]

    def close(self):
        self._mongo_client.close()
