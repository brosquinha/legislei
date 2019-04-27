import json
from datetime import datetime

from mongoengine import *


class Parlamentar(EmbeddedDocument):

    id = StringField(required=True)
    nome = StringField()
    partido = StringField()
    uf = StringField()
    foto = StringField()
    cargo = StringField()

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'partido': self.partido,
            'uf': self.uf,
            'cargo': self.cargo,
            'foto': self.foto
        }

    def to_json(self):
        return json.dumps(self.to_dict(), default=str)


class Orgao(EmbeddedDocument):

    nome = StringField(required=True)
    sigla = StringField()
    cargo = StringField()
    apelido = StringField()

    def to_dict(self):
        return {
            'nome': self.nome,
            'sigla': self.sigla,
            'cargo': self.cargo,
            'apelido': self.apelido
        }


class Proposicao(EmbeddedDocument):

    id = StringField()
    tipo = StringField(required=True)
    ementa = StringField()
    numero = StringField()
    url_documento = URLField(db_field='urlDocumento')
    url_autores = URLField(db_field='urlAutores')
    data_apresentacao = StringField(db_field='dataApresentacao') # DateTimeField
    voto = StringField()
    pauta = StringField()

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero,
            'tipo': self.tipo,
            'ementa': self.ementa,
            'urlDocumento': self.url_documento,
            'urlAutores': self.url_autores,
            'dataApresentacao': self.data_apresentacao,
            'voto': self.voto,
            'pauta': self.pauta
        }


class Evento(EmbeddedDocument):

    id = StringField(required=True)
    nome = StringField(required=True)
    data_inicial = StringField(db_field='dataInicial') # DateTimeField
    data_final = StringField(db_field='dataFinal') # DateTimeField
    url = URLField()
    situacao = StringField()
    presenca = IntField(default=-1)
    pautas = EmbeddedDocumentListField(Proposicao)
    orgaos = EmbeddedDocumentListField(Orgao)

    def set_presente(self):
        self.presenca = 0

    def set_ausencia_evento_nao_esperado(self):
        self.presenca = 1

    def set_ausencia_evento_esperado(self):
        self.presenca = 2

    def set_ausente_evento_previsto(self):
        self.presenca = 3

    def to_dict(self):
        dicionario = {
            'id': self.id,
            'nome': self.nome,
            'dataInicial': self.data_inicial,
            'dataFinal': self.data_final,
            'url': self.url,
            'situacao': self.situacao,
            'presenca': self.presenca,
            'pautas': [],
            'orgaos': []
        }
        for orgao in self.orgaos:
            dicionario['orgaos'].append(orgao.to_dict())
        for pauta in self.pautas:
            dicionario['pautas'].append(pauta.to_dict())
        return dicionario


class Relatorio(Document):

    idTemp = StringField()
    parlamentar = EmbeddedDocumentField(Parlamentar, required=True)
    data_inicial = StringField(db_field='dataInicial') # DateTimeField
    data_final = StringField(db_field='dataFinal') # DateTimeField
    aviso_dados = StringField(db_field='mensagem', null=True)
    orgaos = EmbeddedDocumentListField(Orgao)
    proposicoes = EmbeddedDocumentListField(Proposicao)
    eventos_presentes = EmbeddedDocumentListField(Evento, db_field='eventosPresentes')
    eventos_ausentes = EmbeddedDocumentListField(Evento, db_field='eventosAusentes')
    eventos_previstos = EmbeddedDocumentListField(Evento, db_field='eventosPrevistos')
    presenca_relativa = FloatField(db_field='presencaRelativa', default=0.0)
    presenca_absoluta = FloatField(db_field='presencaTotal', default=0.0)
    eventos_ausentes_esperados_total = IntField(db_field='eventosAusentesEsperadosTotal', default=0)
    meta = {'collection': 'relatorios'}

    def _calcular_presenca_relativa(self):
        ausencia_relativa = len([x for x in self.eventos_ausentes if x.presenca > 1])
        try:
            return 100 * len(self.eventos_presentes) / (ausencia_relativa + len(self.eventos_presentes))
        except ZeroDivisionError:
            return 0 if len(self.eventos_presentes) == 0 else 100

    def _calcular_presenca_absoluta(self):
        try:
            return 100 * len(self.eventos_presentes) / (len(self.eventos_ausentes) + len(self.eventos_presentes))
        except ZeroDivisionError:
            return 0 if len(self.eventos_presentes) == 0 else 100

    def to_dict(self):
        relatorio = {
            '_id': str(self.pk),
            'parlamentar': self.parlamentar.to_dict(),
            'mensagem': self.aviso_dados,
            'dataInicial': self.data_inicial,
            'dataFinal': self.data_final,
            'orgaos': [],
            'proposicoes': [],
            'eventosPresentes': [],
            'eventosAusentes': [],
            'eventosPrevistos': [],
            'presencaRelativa': '{0:.2f}%'.format(self._calcular_presenca_relativa()),
            'presencaTotal': '{0:.2f}%'.format(self._calcular_presenca_absoluta()),
            'eventosAusentesEsperadosTotal': self.eventos_ausentes_esperados_total
        }
        for orgao in self.orgaos:
            relatorio['orgaos'].append(orgao.to_dict())
        for proposicao in self.proposicoes:
            relatorio['proposicoes'].append(proposicao.to_dict())
        for evento in self.eventos_presentes:
            relatorio['eventosPresentes'].append(evento.to_dict())
        for evento in self.eventos_ausentes:
            relatorio['eventosAusentes'].append(evento.to_dict())
        for evento in self.eventos_previstos:
            relatorio['eventosPrevistos'].append(evento.to_dict())
        return relatorio
    
    def to_json(self):
        return json.dumps(self.to_dict(), default=str)
