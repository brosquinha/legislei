from mongoengine import StringField, IntField, EmbeddedDocument, EmbeddedDocumentListField

from legislei.models.relatorio import Parlamentar

class Inscricoes(EmbeddedDocument):

    intervalo = IntField()
    parlamentares = EmbeddedDocumentListField(Parlamentar)