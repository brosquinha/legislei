import json
import os
import unittest
import warnings
from datetime import datetime
from unittest.mock import patch

from bson import ObjectId
from mongoengine import connect

from legislei.app import app
from legislei.exceptions import AppError, InvalidModelId
from legislei.models.avaliacoes import Avaliacoes
from legislei.models.inscricoes import Inscricoes
from legislei.models.relatorio import Evento, Orgao, Parlamentar, Proposicao, Relatorio
from legislei.models.user import User


class TestApp(unittest.TestCase):

    db = None
    
    @classmethod
    def setUpClass(cls):
        TestApp.db = connect('legislei-testing', host=os.environ.get("MONGODB_HOST", "localhost"), port=int(os.environ.get("MONGODB_PORT", "27017")))
        TestApp.db.drop_database("legislei-testing")
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        os.environ["MONGODB_DBNAME"] = "legislei-testing"
        os.environ["HOST_ENDPOINT"] = ''
        set_up_db(TestApp.db)
        self.app = app.test_client()

    def tearDown(self):
        TestApp.db.drop_database("legislei-testing")

    def test_home_page(self):
        actual = self.app.get("/")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(b"Projeto Legislei", actual.data)

    def test_consultar_page(self):
        actual = self.app.get("/consultar")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Consultar político".encode('utf-8'), actual.data)

    def test_relatorio_no_params(self):
        actual = self.app.get("/relatorio")
        self.assertEqual(actual.status_code, 400)

    def test_relatorio_from_db(self):
        actual = self.app.get("/relatorio?parlamentar=123&data=2019-01-07&parlamentarTipo=BR1&dias=7")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(b"ParlamentarTeste", actual.data)

    def test_get_relatorio_by_id(self):
        actual = self.app.get("/relatorio/5c264b5e3a5efd576ecaf48e")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(b"ParlamentarTeste", actual.data)

    def test_get_relatorio_no_relatorio(self):
        actual = self.app.get("/relatorio/4c264b5e3a5efd576ecaf48e")
        self.assertEqual(actual.status_code, 400)
        self.assertIn(u"Relatório não encontrado".encode("utf-8"), actual.data)

    def test_avaliar_item_existente(self):
        login(self.app, "test", "123")
        actual = self.app.post(
            "/avaliar",
            data={
                "id": "5c264b5e3a5efd576ecaf48e",
                "avaliacao": "3",
                "avaliado": "123",
            }
        )
        self.assertEqual(actual.status_code, 201)
        self.assertEqual(actual.data, b"Created")

    def test_avaliar_item_novo(self):
        login(self.app, "test", "123")
        actual = self.app.post(
            "/avaliar",
            data={
                "id": "5c264b5e3a5efd576ecaf48e",
                "avaliacao": "1",
                "avaliado": "12345",
            }
        )
        self.assertEqual(actual.status_code, 201)
        self.assertEqual(actual.data, b"Created")

    def test_avaliar_sem_login(self):
        actual = self.app.post(
            "/avaliar",
            data={
                "id": "5c264b5e3a5efd576ecaf48e",
                "avaliacao": "3",
                "avaliado": "123",
            }
        )
        self.assertEqual(actual.status_code, 401)
        self.assertIn(u"Não autorizado".encode('utf-8'), actual.data)

    def test_avaliar_relatorio_inexistente(self):
        login(self.app, "test", "123")
        actual = self.app.post(
            "/avaliar",
            data={
                "id": "4c264b5e3a5efd576ecaf48e",
                "avaliacao": "3",
                "avaliado": "123",
            }
        )
        self.assertEqual(actual.status_code, 400)
        self.assertEqual(b"Report not found", actual.data)

    def test_avaliar_avaliado_inexistente(self):
        login(self.app, "test", "123")
        actual = self.app.post(
            "/avaliar",
            data={
                "id": "5c264b5e3a5efd576ecaf48e",
                "avaliacao": "3",
                "avaliado": "987",
            }
        )
        self.assertEqual(actual.status_code, 400)
        self.assertEqual(b"Item not found", actual.data)

    def test_minhas_avaliacoes(self):
        login(self.app, "test", "123")
        actual = self.app.get("/minhasAvaliacoes")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Minhas avaliações".encode('utf-8'), actual.data)
        self.assertIn(b"ParlamentarTeste", actual.data)

    def test_minhas_avaliacoes_parlamentar(self):
        login(self.app, "test", "123")
        actual = self.app.get("/minhasAvaliacoes?parlamentarTipo=BR1&parlamentar=123")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(b"ParlamentarTeste", actual.data)
        self.assertIn(b"Saldo total: 1", actual.data)

    def test_minhas_avaliacoes_parlamentar_sem_avaliacoes(self):
        login(self.app, "test", "123")
        actual = self.app.get("/minhasAvaliacoes?parlamentarTipo=BR1&parlamentar=12345")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Nenhuma avaliação".encode('utf-8'), actual.data)

    def test_nova_inscricao_home(self):
        login(self.app, "test", "123")
        actual = self.app.get("/novaInscricao")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Nova inscrição".encode('utf-8'), actual.data)

    @patch("legislei.inscricoes.obter_parlamentar")
    def test_nova_inscricao_primeira_inscricao(
            self, mock_obter_parlamentar):
        mock_obter_parlamentar.return_value = set_up_parlamentar()
        login(self.app, "test", "123")
        User.objects(username="test").update_one(unset__inscricoes=None)
        actual = self.app.post(
            "/novaInscricao",
            data={
                "parlamentarTipo": "BR",
                "parlamentar": "123"
            }, follow_redirects=True
        )
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Minhas avaliações".encode("utf-8"), actual.data)
        self.assertIn(b"ParlamentarTeste", actual.data)

    @patch("legislei.inscricoes.obter_parlamentar")
    def test_nova_inscricao_mais_uma(
            self, mock_obter_parlamentar):
        warnings.simplefilter("ignore") # Details: https://github.com/MongoEngine/mongoengine/issues/1491
        par = Parlamentar()
        par.nome = "Parlamentar2Teste"
        par.cargo = "BR"
        par.id = "12345"
        mock_obter_parlamentar.return_value = par
        login(self.app, "test", "123")
        actual = self.app.post(
            "/novaInscricao",
            data={
                "parlamentarTipo": "BR",
                "parlamentar": "12345"
            }, follow_redirects=True
        )
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Minhas avaliações".encode("utf-8"), actual.data)
        self.assertIn(b"ParlamentarTeste", actual.data)
        self.assertIn(b"Parlamentar2Teste", actual.data)

    @patch("builtins.print")
    @patch("legislei.app.obter_parlamentar")
    def test_nova_inscricao_erro_modelo(
            self, mock_obter_parlamentar, mock_print):
        def fake(*args):
            raise AppError("Erro")
        mock_obter_parlamentar.side_effect = fake
        login(self.app, "test", "123")
        actual = self.app.post(
            "/novaInscricao",
            data={
                "parlamentarTipo": "BR",
                "parlamentar": "123"
            }, follow_redirects=True
        )
        self.assertEqual(actual.status_code, 500)
        self.assertIn(b"Erro", actual.data)

    def test_minhas_avaliacoes_api(self):
        login(self.app, "test", "123")
        actual = self.app.get('/API/minhasAvaliacoes?parlamentar=123&parlamentarTipo=BR1')
        self.assertEqual(actual.status_code, 200)
        self.assertIn(b"ParlamentarTeste", actual.data)
        json.loads(actual.data.decode('utf-8')) #OK if doesnt raise error

    def test_minhas_avaliacoes_api_no_params(self):
        login(self.app, "test", "123")
        actual = self.app.get("/API/minhasAvaliacoes?parlamentar=123")
        self.assertEqual(actual.status_code, 400)
        json.loads(actual.data.decode('utf-8'))

    def test_relatorio_api(self):
        actual = self.app.get("/API/relatorio?parlamentar=123&parlamentarTipo=BR1&data=2019-01-07&dias=7")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("ParlamentarTeste", actual_data)
        json.loads(actual_data)

    def test_relatorio_api_no_params(self):
        actual = self.app.get("/API/relatorio?parlamentar=123")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 400)
        json.loads(actual_data)

    def test_minhas_inscricoes_api_remover_parlamentar(self):
        login(self.app, "test", "123")
        actual = self.app.delete("/API/minhasInscricoes/BR1/123")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("Ok", actual_data)
        json.loads(actual_data)

    def test_minhas_inscricoes_api_remover_parlamentar_model_invalido(self):
        login(self.app, "test", "123")
        actual = self.app.delete("/API/minhasInscricoes/naoexiste/123")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 400)
        json.loads(actual_data)

    def test_minhas_inscricoes_api_config(self):
        login(self.app, "test", "123")
        actual = self.app.post(
            "/API/minhasInscricoes/config",
            data={
                "periodo": 7
            }
        )
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("7", actual_data)
        json.loads(actual_data)

    def test_minhas_inscricoes_api_config_periodo_invalido(self):
        login(self.app, "test", "123")
        actual = self.app.post(
            "/API/minhasInscricoes/config",
            data={
                "periodo": "invalido"
            }
        )
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 400)
        json.loads(actual_data)

    def test_modelos_estaduais_api(self):
        actual = self.app.get("/API/models/estaduais")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("SP", actual_data)
        json.loads(actual_data)

    def test_modelos_municipais_api(self):
        actual = self.app.get("/API/models/municipais")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("PAULO", actual_data)
        json.loads(actual_data)

    @patch("legislei.app.obter_parlamentares")
    def test_obter_parlamentares_api(
            self, mock_obter_parlamentares):
        mock_obter_parlamentares.return_value = [
            {'id': '123', 'nome': 'ParlamentarTeste'},
            {'id': '12345', 'nome': 'Parlamentar2Teste'}
        ]
        actual = self.app.get("/API/parlamentares/BR1")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("ParlamentarTeste", actual_data)
        self.assertIn("Parlamentar2Teste", actual_data)
        json.loads(actual_data)

    @patch("legislei.app.obter_parlamentares")
    def test_obter_parlamentares_api_model_error(
            self, mock_obter_parlamentares):
        def fake(*args, **kwargs):
            raise AppError('Erro')
        mock_obter_parlamentares.side_effect = fake
        actual = self.app.get("/API/parlamentares/BR1")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 500)
        self.assertIn("Erro", actual_data)
        json.loads(actual_data)

    @patch("legislei.app.obter_parlamentares")
    def test_obter_parlamentares_api_invalid_model(
            self, mock_obter_parlamentares):
        def fake(*args, **kwargs):
            raise InvalidModelId('Erro')
        mock_obter_parlamentares.side_effect = fake
        actual = self.app.get("/API/parlamentares/BR1")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 400)
        self.assertIn(u"Cargo não existe", actual_data)
        json.loads(actual_data)

    @patch("legislei.app.obter_parlamentar")
    def test_obter_parlamentar_api(
            self, mock_obter_parlamentar):
        par = Parlamentar()
        par.nome = "ParlamentarTeste"
        par.cargo = "BR"
        par.id = "123"
        mock_obter_parlamentar.return_value = par
        actual = self.app.get("/API/parlamentares/BR1/123")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("ParlamentarTeste", actual_data)
        json.loads(actual_data)

    @patch("legislei.app.obter_parlamentar")
    def test_obter_parlamentar_api_model_error(
            self, mock_obter_parlamentar):
        def fake(*args, **kwargs):
            raise AppError('Erro')
        mock_obter_parlamentar.side_effect = fake
        actual = self.app.get("/API/parlamentares/BR1/123")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 500)
        self.assertIn("Erro", actual_data)
        json.loads(actual_data)

    @patch("legislei.app.obter_parlamentar")
    def test_obter_parlamentar_api_invalid_model(
            self, mock_obter_parlamentar):
        def fake(*args, **kwargs):
            raise InvalidModelId('Erro')
        mock_obter_parlamentar.side_effect = fake
        actual = self.app.get("/API/parlamentares/BR1/123")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 400)
        self.assertIn("Cargo não existe", actual_data)
        json.loads(actual_data)

    def test_relatorios_parlamentar_api(self):
        actual = self.app.get("/API/relatorios/BR1/123")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("ParlamentarTeste", actual_data)
        json.loads(actual_data)

    def test_registrar_home(self):
        actual = self.app.get("/registrar")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("Criar uma conta", actual_data)

    def test_registrar_ok(self):
        actual = self.app.post(
            '/registrar',
            data={
                "name": "mrTest",
                "password": "12345",
                "password_confirmed": "12345",
                "email": "mrtest@test.com"
            }, follow_redirects=True
        )
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("Entrar", actual_data)

    def test_registrar_senhas_diferentes(self):
        actual = self.app.post(
            "/registrar",
            data={
                "name": "mrTest",
                "password": "12345",
                "password_confirmed": "54321",
                "email": "mrtest@test.com"
            }, follow_redirects=True
        )
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Requisitos não atingidos", actual_data)

    def test_registrar_username_existente(self):
        actual = self.app.post(
            "/registrar",
            data={
                "name": "test",
                "password": "12345",
                "password_confirmed": "12345",
                "email": "mrtest@test.com"
            }, follow_redirects=True
        )
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Usuário e/ou email já existem", actual_data)

    def test_registrar_email_existente(self):
        actual = self.app.post(
            "/registrar",
            data={
                "name": "mrTest",
                "password": "12345",
                "password_confirmed": "12345",
                "email": "test@email.com"
            }, follow_redirects=True
        )
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Usuário e/ou email já existem", actual_data)

    def test_login_home(self):
        actual = self.app.get("/login")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("Entrar", actual_data)

    def test_login_ok(self):
        actual = self.app.post(
            "/login",
            data={
                "name": "test",
                "password": "123"
            }, follow_redirects=True
        )
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Minhas inscrições", actual_data)

    def test_login_incorreto(self):
        actual = self.app.post(
            "/login",
            data={
                "name": "test",
                "password": "12345"
            }, follow_redirects=True
        )
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Usuário/senha incorretos", actual_data)

    def test_logout(self):
        login(self.app, "test", "123")
        actual = self.app.get("/logout", follow_redirects=True)
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Projeto Legislei", actual_data)


def login(client, username, password):
    return client.post('/login', data={
        "name": username,
        "password": password
    }, follow_redirects=True)


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
    orgaos_evento = [Orgao(
        nome="ÓrgãoTeste",
        sigla="OT",
        cargo="None",
        apelido="OhTe"
    )]
    eventos_presentes = [Evento(
        id="12345",
        nome="Evento teste",
        data_inicial=datetime(2019, 1, 1),
        data_final=datetime(2019, 1, 1),
        url="http://url.com",
        situacao="Encerrada",
        presenca=0,
        orgaos=orgaos_evento
    )]
    eventos_ausentes = [Evento(
        id="123",
        nome="Evento teste",
        data_inicial=datetime(2019, 1, 1),
        data_final=datetime(2019, 1, 1),
        url="http://url.com",
        situacao="Cancelada",
        presenca=1,
        orgaos=orgaos_evento
    )]
    Relatorio(
        pk=ObjectId("5c264b5e3a5efd576ecaf48e"),
        parlamentar=parlamentar_test,
        proposicoes=[],
        data_inicial=datetime(2019, 1, 1),
        data_final=datetime(2019, 1, 7),
        orgaos=[],
        eventos_presentes=eventos_presentes,
        eventos_ausentes=eventos_ausentes,
        eventos_previstos=[],
    ).save()
    Avaliacoes(
        email="test@email.com",
        parlamentar=parlamentar_test,
        avaliacao="1",
        avaliado={
            "url": "url",
            "situacao": "Cancelada",
            "dataFinal": datetime(2019, 1, 1),
            "orgaos": [
                {
                    "sigla": "OT",
                    "nome": "ÓrgãoTeste",
                    "apelido": "OhTe",
                    "cargo": None
                }
            ],
            "dataInicial": datetime(2019, 1, 1),
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
    User(
        username="test",
        email="test@email.com",
        password="$pbkdf2-sha256$16$ZOwdg9A6R2itlTKm9N57bw$J8ut3l2pGwngIOdLZeT/LMHCY/CW75wNZOAk6k6sP1c",
        inscricoes=inscricoes
    ).save()
