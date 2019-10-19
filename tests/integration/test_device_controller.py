import json
import warnings

from .utils import *
from legislei import controllers
from legislei.models.user import User

class TestDeviceController(ControllerHelperTester):

    def setUp(self):
        super().setUp()
        warnings.simplefilter("ignore")

    
    def test_get_dispositivos_sucesso(self):
        login_header = login_api(self.app, "test", "123")
        user = User.objects(username="test").first()
        actual = self.app.get(
            "/v1/usuarios/dispositivos",
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertIn("dispositivo", str(actual_data))
        self.assertIn("---token---", str(actual_data))

    def test_get_dispositivos_sem_login(self):
        user_id = User.objects(username="test").first().pk
        actual = self.app.get(
            "/v1/usuarios/dispositivos".format(user_id)
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 401)
        self.assertIn("message", actual_data)

    def test_post_dispositivos_sucesso(self):
        login_header = login_api(self.app, "test", "123")
        user = User.objects(username="test").first()
        actual = self.app.post(
            "/v1/usuarios/dispositivos",
            data=json.dumps({
                "uuid": "1414",
                "token": "---token2---",
                "name": "outro_dispositivo",
                "os": "iOS"
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 201)
        self.assertEqual("Criado", actual_data["message"])
        self.assertEqual(len(user.reload().devices), 2)

    def test_post_dispositivos_dispositivo_com_mesmo_uuid_existente(self):
        login_header = login_api(self.app, "test", "123")
        user = User.objects(username="test").first()
        actual = self.app.post(
            "/v1/usuarios/dispositivos",
            data=json.dumps({
                "uuid": "14",
                "token": "---token2---",
                "name": "outro_dispositivo",
                "os": "iOS"
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 422)
        self.assertEqual("Dispositivo já existe", actual_data["message"])
        self.assertEqual(len(user.reload().devices), 1)

    def test_post_dispositivos_faltando_parametros_obrigatorios(self):
        login_header = login_api(self.app, "test", "123")
        user_id = User.objects(username="test").first().pk
        actual = self.app.post(
            "/v1/usuarios/dispositivos".format(user_id),
            data=json.dumps({
                "uuid": "1414",
                "token": "---token2---",
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertIn("message", actual_data)

    def test_post_dispositivos_parametros_invalidos(self):
        login_header = login_api(self.app, "test", "123")
        user_id = User.objects(username="test").first().pk
        actual = self.app.post(
            "/v1/usuarios/dispositivos".format(user_id),
            data=json.dumps({
                "uuid": "1414",
                "token": True,
                "name": "outro_dispositivo"
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertIn("message", actual_data)

    def test_post_dispositivos_sem_login(self):
        user_id = User.objects(username="test").first().pk
        actual = self.app.post(
            "/v1/usuarios/dispositivos".format(user_id),
            data=json.dumps({
                "uuid": "1414",
                "token": "---token2---",
                "name": "outro_dispositivo",
                "os": "iOS"
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 401)
        self.assertIn("message", actual_data)

    def test_patch_dispositivos_sucesso(self):
        login_header = login_api(self.app, "test", "123")
        user = User.objects(username="test").first()
        actual = self.app.patch(
            "/v1/usuarios/dispositivos/14",
            data=json.dumps({
                "active": False
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertEqual("Ok", actual_data["message"])
        self.assertFalse(user.reload().devices[0].active)

    def test_patch_dispositivos_parametro_inexistente(self):
        login_header = login_api(self.app, "test", "123")
        user = User.objects(username="test").first()
        actual = self.app.patch(
            "/v1/usuarios/dispositivos/14",
            data=json.dumps({
                "naoexisto": True
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertIn("message", actual_data)
        self.assertNotIn("naoexisto", user.reload().devices[0].to_json())

    def test_patch_dispositivos_dispositivo_inexistente(self):
        login_header = login_api(self.app, "test", "123")
        user = User.objects(username="test").first()
        actual = self.app.patch(
            "/v1/usuarios/dispositivos/124578",
            data=json.dumps({
                "active": False
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertEqual("Dispositivo não existe", actual_data["message"])

    def test_patch_dispositivos_parametro_invalido(self):
        login_header = login_api(self.app, "test", "123")
        user = User.objects(username="test").first()
        actual = self.app.patch(
            "/v1/usuarios/dispositivos/14",
            data=json.dumps({
                "active": "invalido"
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertIn("message", actual_data)

    def test_patch_dispositivos_sem_login(self):
        user = User.objects(username="test").first()
        actual = self.app.patch(
            "/v1/usuarios/dispositivos/14",
            data=json.dumps({
                "active": False
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 401)
        self.assertIn("message", actual_data)

    def test_delete_dispositivos_sucesso(self):
        login_header = login_api(self.app, "test", "123")
        user = User.objects(username="test").first()
        actual = self.app.delete(
            "/v1/usuarios/dispositivos/14",
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertEqual("Apagado", actual_data["message"])
        self.assertEqual(len(user.reload().devices), 0)

    def test_delete_dispositivos_sem_login(self):
        user = User.objects(username="test").first()
        actual = self.app.delete(
            "/v1/usuarios/dispositivos/14"
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 401)
        self.assertIn("message", actual_data)
