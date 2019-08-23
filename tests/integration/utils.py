import json
import os
from datetime import datetime
from unittest import TestCase

import pytz
from bson import ObjectId
from mongoengine import connect

from legislei.app import app
from legislei.models.avaliacoes import Avaliacoes
from legislei.models.inscricoes import Inscricoes
from legislei.models.relatorio import Evento, Orgao, Parlamentar, Relatorio
from legislei.models.user import User


class ControllerHelperTester(TestCase):
    db = None
    
    @classmethod
    def setUpClass(cls):
        cls.db = connect('legislei-testing', host=os.environ.get("MONGODB_HOST", "localhost"), port=int(os.environ.get("MONGODB_PORT", "27017")))
        cls.db.drop_database("legislei-testing")
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        os.environ["MONGODB_DBNAME"] = "legislei-testing"
        os.environ["HOST_ENDPOINT"] = ''
        set_up_db(self.db)
        self.app = app.test_client()

    def tearDown(self):
        self.db.drop_database("legislei-testing")


def login(client, username, password):
    return client.post('/login', data={
        "name": username,
        "password": password
    }, follow_redirects=True)


def login_api(client, username, password):
    response = client.post(
        '/v1/usuarios/token_acesso',
        data=json.dumps({
            'username': username,
            'senha': password
        }),
        content_type='application/json'
    )
    response = json.loads(response.data.decode('utf-8'))
    return {'Authorization': response["token"]}


def logout(client):
    return client.get('/logout', follow_redirects=True)


def set_up_parlamentar():
    par = Parlamentar()
    par.nome = "ParlamentarTeste"
    par.foto = "url"
    par.id = "123"
    par.partido = "Partido"
    par.cargo = "BR1"
    par.uf = "ES"
    return par


def set_up_db(db):
    parlamentar_test = set_up_parlamentar()
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    orgaos_evento = [Orgao(
        nome="ÓrgãoTeste",
        sigla="OT",
        cargo="None",
        apelido="OhTe"
    )]
    eventos_presentes = [Evento(
        id="12345",
        nome="Evento teste",
        data_inicial=brasilia_tz.localize(datetime(2019, 1, 1)),
        data_final=brasilia_tz.localize(datetime(2019, 1, 1)),
        url="http://url.com",
        situacao="Encerrada",
        presenca=0,
        orgaos=orgaos_evento
    )]
    eventos_ausentes = [Evento(
        id="123",
        nome="Evento teste",
        data_inicial=brasilia_tz.localize(datetime(2019, 1, 1)),
        data_final=brasilia_tz.localize(datetime(2019, 1, 1)),
        url="http://url.com",
        situacao="Cancelada",
        presenca=1,
        orgaos=orgaos_evento
    )]
    Relatorio(
        pk=ObjectId("5c264b5e3a5efd576ecaf48e"),
        parlamentar=parlamentar_test,
        proposicoes=[],
        data_inicial=brasilia_tz.localize(datetime(2018, 12, 31)),
        data_final=brasilia_tz.localize(datetime(2019, 1, 7)),
        orgaos=[],
        eventos_presentes=eventos_presentes,
        eventos_ausentes=eventos_ausentes,
        eventos_previstos=[],
    ).save()
    Avaliacoes(
        pk=ObjectId("5c5116f5c3acc80004eada0a"),
        email="test@email.com",
        parlamentar=parlamentar_test,
        avaliacao="1",
        avaliado={
            "url": "url",
            "situacao": "Cancelada",
            "dataFinal": brasilia_tz.localize(datetime(2019, 1, 1)),
            "orgaos": [
                {
                    "sigla": "OT",
                    "nome": "ÓrgãoTeste",
                    "apelido": "OhTe",
                    "cargo": None
                }
            ],
            "dataInicial": brasilia_tz.localize(datetime(2019, 1, 1)),
            "presenca": 1,
            "nome": "Evento teste",
            "id": "123"
        },
        relatorioId=ObjectId("5c264b5e3a5efd576ecaf48e"),
    ).save()
    inscricoes = Inscricoes(
        parlamentares=[parlamentar_test],
        intervalo=7
    )
    User.drop_collection()
    User(
        username="test",
        email="test@email.com",
        password="$pbkdf2-sha256$16$ZOwdg9A6R2itlTKm9N57bw$J8ut3l2pGwngIOdLZeT/LMHCY/CW75wNZOAk6k6sP1c",
        inscricoes=inscricoes
    ).save()