import json
from datetime import datetime

class Relatorio():

    def __init__(self):
        self._parlamentar_id = None
        self._parlamentar_nome = None
        self._parlamentar_partido = None
        self._parlamentar_uf = None
        self._parlamentar_foto = None
        self._parlamentar_cargo = None

        self._data_inicial = datetime.now()
        self._data_final = datetime.now()
        self._aviso_dados = None #mensagem

        self._orgaos = []
        self._proposicoes = []
        self._eventos_presentes = []
        self._eventos_ausentes = []
        self._eventos_previstos = []
        self._presenca_relativa = None
        self._presenca_absoluta = None
        self._eventos_ausentes_esperados_total = None

    def get_parlamentar_id(self):
        return self._parlamentar_id

    def set_parlamentar_id(self, id):
        self._parlamentar_id = str(id)
    
    def get_parlamentar_nome(self):
        return self._parlamentar_nome
    
    def set_parlamentar_nome(self, nome):
        self._parlamentar_nome = nome

    def get_parlamentar_partido(self):
        return self._parlamentar_partido

    def set_parlamentar_partido(self, partido):
        self._parlamentar_partido = partido

    def get_parlamentar_uf(self):
        return self._parlamentar_uf

    def set_parlamentar_uf(self, uf):
        self._parlamentar_uf = uf

    def get_parlamentar_foto(self):
        return self._parlamentar_foto

    def set_parlamentar_foto(self, url):
        self._parlamentar_foto = url

    def get_parlamentar_cargo(self):
        return self._parlamentar_cargo

    def set_parlamentar_cargo(self, cargo):
        self._parlamentar_cargo = cargo.upper()

    def get_data_inicial(self):
        return self._data_inicial

    def set_data_inicial(self, data):
        if isinstance(data, datetime):
            self._data_inicial = data

    def get_data_final(self):
        return self._data_final

    def set_data_final(self, data):
        if isinstance(data, datetime):
            self._data_final = data

    def get_aviso_dados(self):
        return self._aviso_dados

    def set_aviso_dados(self, aviso):
        self._aviso_dados = aviso

    def get_orgaos(self):
        return self._orgaos
    
    def add_orgao(self, orgao):
        if isinstance(orgao, Orgao):
            self._orgaos.append(orgao)

    def get_proposicoes(self):
        return self._proposicoes

    def add_proposicao(self, proposicao):
        if isinstance(proposicao, Proposicao):
            self._proposicoes.append(proposicao)

    def get_eventos_presentes(self):
        return self._eventos_presentes

    def add_evento_presente(self, evento):
        if isinstance(evento, Evento):
            self._eventos_presentes.append(evento)

    def get_eventos_ausentes(self):
        return self._eventos_ausentes

    def add_evento_ausente(self, evento):
        if isinstance(evento, Evento):
            self._eventos_ausentes.append(evento)

    def get_eventos_previstos(self):
        return self._eventos_previstos

    def add_evento_previsto(self, evento):
        if isinstance(evento, Evento):
            self._eventos_previstos.append(evento)

    def get_eventos_ausentes_esperados_total(self):
        return self._eventos_ausentes_esperados_total

    def set_eventos_ausentes_esperados_total(self, total):
        self._eventos_ausentes_esperados_total = total

    def _calcular_presenca_relativa(self):
        ausencia_relativa = len([x for x in self._eventos_ausentes if x.get_presenca() > 1])
        try:
            return 100 * len(self._eventos_presentes) / ausencia_relativa
        except ZeroDivisionError:
            return 0 if len(self._eventos_presentes) == 0 else 100

    def _calcular_presenca_absoluta(self):
        try:
            return 100 * len(self._eventos_presentes) / len(self._eventos_ausentes)
        except ZeroDivisionError:
            return 0if len(self._eventos_presentes) == 0 else 100

    def to_dict(self):
        relatorio = {
            'parlamentar': {
                'id': self._parlamentar_id,
                'nome': self._parlamentar_nome,
                'partido': self._parlamentar_partido,
                'uf': self._parlamentar_uf,
                'cargo': self._parlamentar_cargo,
                'foto': self._parlamentar_foto
            },
            'mensagem': self._aviso_dados,
            'dataInicial': self._data_inicial.strftime("%d/%m/%Y"),
            'dataFinal': self._data_final.strftime("%d/%m/%Y"),
            'orgaos': [],
            'proposicoes': [],
            'eventosPresentes': [],
            'eventosAusentes': [],
            'eventosPrevistos': [],
            'presencaRelativa': '{0:.2f}%'.format(self._calcular_presenca_relativa()),
            'presencaTotal': '{0:.2f}%'.format(self._calcular_presenca_absoluta()),
            'eventosAusentesEsperadosTotal': self._eventos_ausentes_esperados_total
        }
        for orgao in self._orgaos:
            relatorio['orgaos'].append(orgao.to_dict())
        for proposicao in self._proposicoes:
            relatorio['proposicoes'].append(proposicao.to_dict())
        for evento in self._eventos_presentes:
            relatorio['eventosPresentes'].append(evento.to_dict())
        for evento in self._eventos_ausentes:
            relatorio['eventosAusentes'].append(evento.to_dict())
        for evento in self._eventos_previstos:
            relatorio['eventosPrevistos'].append(evento.to_dict())
        return relatorio
    
    def to_json(self):
        return json.dumps(self.to_dict(), default=str)

class Orgao():

    def __init__(self):
        self._nome = None
        self._sigla = None
        self._cargo = None
        self._apelido = None

    def get_nome(self):
        return self._nome

    def set_nome(self, nome):
        self._nome = nome

    def get_sigla(self):
        return self._sigla

    def set_sigla(self, sigla):
        self._sigla = sigla

    def get_cargo(self):
        return self._cargo

    def set_cargo(self, cargo):
        self._cargo = cargo

    def get_apelido(self):
        return self._apelido

    def set_apelido(self, apelido):
        self._apelido = apelido

    def to_dict(self):
        return {
            'nome': self._nome,
            'sigla': self._sigla,
            'cargo': self._cargo,
            'apelido': self._apelido
        }

class Proposicao():

    def __init__(self):
        self._id = None
        self._tipo = None
        self._ementa = None
        self._numero = None
        self._url_documento = None
        self._url_autores = None
        self._data_apresentacao = datetime.now()
        self._voto = None
        self._pauta = None

    def get_id(self):
        return self._id

    def set_id(self, id):
        self._id = id
    
    def get_tipo(self):
        return self._tipo

    def set_tipo(self, tipo):
        self._tipo = tipo

    def get_ementa(self):
        return self._ementa

    def set_ementa(self, ementa):
        self._ementa = ementa

    def get_numero(self):
        return self._numero

    def set_numero(self, numero):
        self._numero = numero

    def get_url_documento(self):
        return self._url_documento

    def set_url_documento(self, url):
        self._url_documento = url

    def get_url_autores(self):
        return self._url_autores

    def set_url_autores(self, url):
        self._url_autores = url

    def get_data_apresentacao(self):
        return self._data_apresentacao

    def set_data_apresentacao(self, data):
        #if isinstance(data, datetime):
        self._data_apresentacao = data

    def get_voto(self):
        return self._voto

    def set_voto(self, voto):
        self._voto = voto

    def get_pauta(self):
        return self._pauta

    def set_pauta(self, pauta):
        self._pauta = pauta

    def to_dict(self):
        return {
            'id': self._id,
            'numero': self._numero,
            'tipo': self._tipo,
            'ementa': self._ementa,
            'urlDocumento': self._url_documento,
            'urlAutores': self._url_autores,
            'dataApresentacao': self._data_apresentacao,
            'voto': self._voto,
            'pauta': self._pauta
        }

class Evento():

    def __init__(self):
        self._id = None
        self._nome = None
        self._data_inicial = datetime.now()
        self._data_final = datetime.now()
        self._url = None
        self._situacao = None
        self._presenca = -1
        self._pautas = []
        self._orgaos = []

    def get_id(self):
        return self._id

    def set_id(self, id):
        self._id = id
    
    def get_nome(self):
        return self._nome

    def set_nome(self, nome):
        self._nome = nome

    def get_data_inicial(self):
        return self._data_inicial

    def set_data_inicial(self, data):
        #if isinstance(data, datetime):
        self._data_inicial = data

    def get_data_final(self):
        return self._data_final

    def set_data_final(self, data):
        #if isinstance(data, datetime):
        self._data_final = data

    def get_url(self):
        return self._url

    def set_url(self, url):
        self._url = url

    def get_situacao(self):
        return self._situacao

    def set_situacao(self, situacao):
        self._situacao = situacao

    def get_presenca(self):
        return self._presenca

    def set_presente(self):
        self._presenca = 0

    def set_ausencia_evento_nao_esperado(self):
        self._presenca = 1

    def set_ausencia_evento_esperado(self):
        self._presenca = 2

    def set_ausente_evento_previsto(self):
        self._presenca = 3

    def get_pautas(self):
        return self._pautas

    def add_pautas(self, proposicao):
        if isinstance(proposicao, Proposicao) or proposicao == None:
            self._pautas.append(proposicao)

    def get_orgaos(self):
        return self._orgaos

    def add_orgaos(self, orgao):
        if isinstance(orgao, Orgao):
            self._orgaos.append(orgao)

    def to_dict(self):
        dicionario = {
            'id': self._id,
            'nome': self._nome,
            'dataInicial': self._data_inicial,
            'dataFinal': self._data_final,
            'url': self._url,
            'situacao': self._situacao,
            'presenca': self._presenca,
            'pautas': [],
            'orgaos': []
        }
        for orgao in self._orgaos:
            dicionario['orgaos'].append(orgao.to_dict())
        for pauta in self._pautas:
            dicionario['pautas'].append(pauta.to_dict())
        return dicionario
