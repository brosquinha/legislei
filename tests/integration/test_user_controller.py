import json

from .utils import *
from legislei import controllers

class TestUserController(ControllerHelperTester):

    def test_usuarios_token_acesso_sucesso(self):
        actual = self.app.post(
            "/v1/usuarios/token_acesso",
            data=json.dumps({
                'username': 'test',
                'senha': '123'
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertIn("token", actual_data)

    def test_usuarios_token_acesso_parametros_ausentes(self):
        actual = self.app.post(
            "/v1/usuarios/token_acesso",
            data=json.dumps({
                'username': 'test'
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertIn("message", actual_data)
        self.assertIn("errors", actual_data)
        self.assertIn("senha", actual_data["errors"])

    def test_usuarios_token_acesso_login_incorreto(self):
        actual = self.app.post(
            "/v1/usuarios/token_acesso",
            data=json.dumps({
                'username': 'test',
                'senha': 'senha_errada'
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 401)
        self.assertEqual(actual_data, {'message': 'Login falhou'})

    def test_post_usuarios_sucesso(self):
        actual = self.app.post(
            "/v1/usuarios",
            data=json.dumps({
                'username': 'test2',
                'senha': '12345',
                'senha_confirmada': '12345',
                'email': 'test2@test.com'
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 201)
        self.assertEqual(actual_data, {'message': 'Criado'})

    def test_post_usuarios_parametros_ausentes(self):
        actual = self.app.post(
            "/v1/usuarios",
            data=json.dumps({
                'username': 'test2',
                'senha': '12345',
                'email': 'test2@test.com'
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertIn("message", actual_data)
        self.assertIn("errors", actual_data)
        self.assertIn("senha_confirmada", actual_data["errors"])

    def test_post_usuarios_senhas_diferentes(self):
        actual = self.app.post(
            "/v1/usuarios",
            data=json.dumps({
                'username': 'test2',
                'senha': '12345',
                'senha_confirmada': '54321',
                'email': 'test2@test.com'
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertEqual(actual_data, {'message': 'Requisitos não atingidos'})

    def test_post_usuarios_username_repetido(self):
        actual = self.app.post(
            "/v1/usuarios",
            data=json.dumps({
                'username': 'test',
                'senha': '12345',
                'senha_confirmada': '12345',
                'email': 'test2@test.com'
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertEqual(actual_data, {'message': 'Usuário e/ou email já existem'})
