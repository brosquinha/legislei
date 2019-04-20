from mongoengine import Document, StringField, IntField, EmbeddedDocumentListField

from legislei.models.relatorio import Parlamentar

class Inscricoes(Document):

    email = StringField()
    intervalo = IntField()
    parlamentares = EmbeddedDocumentListField(Parlamentar)