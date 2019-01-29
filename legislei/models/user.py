from bson.objectid import ObjectId

from mongoengine import *

from legislei.db import MongoDBClient


class User(Document):
    """
    Classe de usuário requerida pelo Flask-Login
    """

    # user_id = ObjectIdField(db_field='_id', required=True, unique=True, primary_key=True)
    user_id = StringField(db_field='_id', required=True, unique=True, primary_key=True)
    username = StringField(min_length=3, unique=True, required=True)
    email = EmailField(unique=True, required=True)
    password = StringField(required=True)
    
    def is_authenticated(self):
        return self.user_id

    def is_active(self):
        return self.user_id

    def is_anonymous(self):
        return self.user_id == None

    def get_id(self):
        return self.user_id

    @staticmethod
    def get_user(id):
        """
        Obtém o usuário com o id fornecido

        :param id: Id de usuário
        :type id: String
        :return: Usuário
        :rtype: User
        """
        mongo_client = MongoDBClient()
        users_col = mongo_client.get_collection('users')
        user = users_col.find_one({'_id': ObjectId(id)})
        mongo_client.close()
        if user:
            return User(id, user['username'], user['email'])
        else:
            return None
