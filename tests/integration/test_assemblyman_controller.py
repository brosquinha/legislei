import json
from unittest.mock import patch

from .utils import *

from legislei import controllers
from legislei.models.relatorio import Parlamentar

class TestAssemblymanController(ControllerHelperTester):
    
    @patch("legislei.controllers.assemblyman_controller.obter_parlamentares")
    def test_parlamentares_casa_sucesso(self, mock_obter_parlamentares):
        mock_obter_parlamentares.return_value = [
            Parlamentar(id='123', nome='ParlamentarTeste'),
            Parlamentar(id='12345', nome='Parlamentar2Teste')
        ]
        actual = self.app.get("/v1/parlamentares/BR2")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("ParlamentarTeste", actual_data)
        self.assertIn("Parlamentar2Teste", actual_data)
        json.loads(actual_data)

    def test_parlamentares_casa_invalida(self):
        actual = self.app.get("/v1/parlamentares/BR3")
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 400)
        self.assertEqual({"message": u"Id de casa legislativa inválido"}, actual_data)

    @patch("legislei.controllers.assemblyman_controller.obter_parlamentar")
    def test_parlamentares_casa_parlamentar_sucesso(self, mock_obter_parlamentar):
        mock_obter_parlamentar.return_value = Parlamentar(id='1', nome='Parlamentar')
        actual = self.app.get("/v1/parlamentares/BR2/1")
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 200)
        self.assertEqual(actual_data["id"], "1")
        self.assertEqual(actual_data["nome"], "Parlamentar")

    @patch("legislei.controllers.assemblyman_controller.obter_parlamentar")
    def test_parlamentares_casa_parlamentar_id_parlamentar_invalido(self, mock_obter_parlamentar):
        mock_obter_parlamentar.return_value = None
        actual = self.app.get("/v1/parlamentares/BR2/99")
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 422)
        self.assertEqual(actual_data, {"message": "Id de parlamentar inválido"})

    def test_parlamentares_casa_parlamentar_id_casa_invalido(self):
        actual = self.app.get("/v1/parlamentares/BR3/1")
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 400)
        self.assertEqual(actual_data, {"message": "Id de casa legislativa inválido"})

    def test_parlamentares_casa_parlamentar_avaliacoes_sucesso(self):
        login_header = login_api(self.app, "test", "123")
        actual = self.app.get("/v1/parlamentares/BR1/123/avaliacoes", headers=login_header)
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 200)
        self.assertIn("ParlamentarTeste", str(actual_data))
        self.assertIn("Evento teste", str(actual_data))

    def test_parlamentares_casa_parlamentar_avaliacoes_sem_login(self):
        actual = self.app.get("/v1/parlamentares/BR1/123/avaliacoes")
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 401)
        self.assertIn("message", actual_data)
