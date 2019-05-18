from mongoengine import Document, StringField, EmbeddedDocumentField, DictField, ObjectIdField

from legislei.models.relatorio import Parlamentar


class Avaliacoes(Document):

    email = StringField()
    parlamentar = EmbeddedDocumentField(Parlamentar)
    avaliacao = StringField()
    avaliado = DictField()
    relatorioId = ObjectIdField()
