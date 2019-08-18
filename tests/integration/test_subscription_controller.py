import json
import warnings
from unittest.mock import patch

from .utils import *
from legislei import controllers
from legislei.models.relatorio import Parlamentar

class TestSubscriptionController(ControllerHelperTester):

    def test_get_usuarios_inscricoes_sucesso(self):
        login_header = login_api(self.app, "test", "123")
        actual = self.app.get("/v1/usuarios/inscricoes", headers=login_header)
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertIn("ParlamentarTeste", str(actual_data))
        self.assertIn("7", str(actual_data))

    def test_get_usuarios_inscricoes_sem_login(self):
        actual = self.app.get("/v1/usuarios/inscricoes")
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 401)
        self.assertIn("message", actual_data)

    @patch("legislei.inscricoes.obter_parlamentar")    
    def test_post_usuarios_inscricoes_sucesso(self, mock_obter_parlamentar):
        warnings.simplefilter("ignore")
        mock_obter_parlamentar.return_value = Parlamentar(id="12345", cargo="BR1")
        login_header = login_api(self.app, "test", "123")
        actual = self.app.post(
            "/v1/usuarios/inscricoes",
            data=json.dumps({
                'casa': 'BR1',
                'parlamentar': '12345'
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 201)
        self.assertEqual(actual_data, {"message": "Criada"})

    def test_post_usuarios_inscricoes_sem_login(self):
        actual = self.app.post(
            "/v1/usuarios/inscricoes",
            data=json.dumps({
                'casa': 'BR1',
                'parlamentar': '12345'
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 401)
        self.assertIn("message", actual_data)

    def test_post_usuarios_inscricoes_parametros_ausentes(self):
        login_header = login_api(self.app, "test", "123")
        actual = self.app.post(
            "/v1/usuarios/inscricoes",
            data=json.dumps({
                'casa': 'BR1',
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertIn("message", actual_data)
        self.assertIn("errors", actual_data)
        self.assertIn("parlamentar", actual_data["errors"])

    def test_post_usuarios_inscricoes_casa_invalida(self):
        login_header = login_api(self.app, "test", "123")
        actual = self.app.post(
            "/v1/usuarios/inscricoes",
            data=json.dumps({
                'casa': 'BR3',
                'parlamentar': '123'
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertEqual(actual_data, {'message': 'Id de casa legislativa inválido'})

    def test_put_usuarios_inscricoes_sucesso(self):
        login_header = login_api(self.app, "test", "123")
        actual = self.app.put(
            "/v1/usuarios/inscricoes",
            data=json.dumps({'intervalo': 14}),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertEqual(actual_data, {'message': 'Configurações de inscrições atualizadas'})

    def test_put_usuarios_inscricoes_sem_login(self):
        actual = self.app.put(
            "/v1/usuarios/inscricoes",
            data=json.dumps({'intervalo': 14}),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 401)
        self.assertIn("message", actual_data)

    def test_put_usuarios_inscricoes_sem_intervalo(self):
        actual = self.app.put(
            "/v1/usuarios/inscricoes",
            data=json.dumps({}),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertIn("message", actual_data)
        self.assertIn("errors", actual_data)
        self.assertIn("intervalo", actual_data["errors"])

    def test_delete_usuarios_inscricoes_casa_parlamentar_sucesso(self):
        login_header = login_api(self.app, "test", "123")
        actual = self.app.delete("/v1/usuarios/inscricoes/BR1/123", headers=login_header)
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertEqual(actual_data, {'message': 'Inscrição deletada'})

    def test_delete_usuarios_inscricoes_casa_parlamentar_sem_login(self):
        actual = self.app.delete("/v1/usuarios/inscricoes/BR1/123")
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 401)
        self.assertIn("message", actual_data)

    def test_delete_usuarios_inscricoes_casa_parlamentar_casa_invalida(self):
        login_header = login_api(self.app, "test", "123")
        actual = self.app.delete("/v1/usuarios/inscricoes/BR3/123", headers=login_header)
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertEqual(actual_data, {'message': 'Id de casa legislativa inválido'})
