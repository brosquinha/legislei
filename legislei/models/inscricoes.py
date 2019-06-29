from mongoengine import StringField, IntField, EmbeddedDocument, EmbeddedDocumentListField

from legislei.models.relatorio import Parlamentar

class Inscricoes(EmbeddedDocument):

    intervalo = IntField(choices=[7, 14, 21, 28])
    parlamentares = EmbeddedDocumentListField(Parlamentar)