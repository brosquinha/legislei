from bson.objectid import ObjectId

from mongoengine import Document, StringField, EmailField, StringField


class User(Document):
    """
    Classe de usuário requerida pelo Flask-Login
    """

    username = StringField(min_length=3, unique=True, required=True)
    email = EmailField(unique=True, required=True)
    password = StringField(required=True)
    meta = {'collection': 'users'}
    
    def is_authenticated(self):
        return str(self.pk)

    def is_active(self):
        return str(self.pk)

    def is_anonymous(self):
        return self.pk == None

    def get_id(self):
        return str(self.pk)
