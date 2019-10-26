import unittest
import warnings

from mongoengine import connect

from legislei.exceptions import InvalidParametersError, UserDoesNotExist
from legislei.models.user import User, UserDevice
from legislei.services.dispositivos import Dispositivo


class TestDispositivos(unittest.TestCase):
    
    def setUp(self):
        connect('mongoenginetest', host='mongomock://localhost')
        warnings.simplefilter("ignore")

    def tearDown(self):
        User.drop_collection()

    def test_obter_dispositivos_de_usuario_sucesso(self):
        device1 = UserDevice(
            id="1",
            token="---token1---",
            active=False,
            name="Dispositivo1",
            os="Android 14"
        )
        device2 = UserDevice(
            id="2",
            token="---token2---",
            name="Dispositivo2",
            os="Android 14"
        )
        user = User(
            username="user",
            email="user@email.com",
            password="secret",
            devices=[device1, device2]
        ).save()

        actual = Dispositivo().obter_dispositivos_de_usuario(user.id)

        self.assertEqual(actual, [device1, device2])

    def test_obter_dispositivos_de_usuario_lista_vazia(self):
        user = User(
            username="user",
            email="user@email.com",
            password="secret",
            devices=[]
        ).save()

        actual = Dispositivo().obter_dispositivos_de_usuario(user.id)

        self.assertEqual(actual, [])

    def test_obter_dispositivos_de_usuario_sem_devices(self):
        user = User(
            username="user",
            email="user@email.com",
            password="secret"
        ).save()

        actual = Dispositivo().obter_dispositivos_de_usuario(user.id)

        self.assertEqual(actual, [])

    def test_obter_dispositivos_de_usuario_usuario_inexistente(self):
        with self.assertRaises(UserDoesNotExist):
            Dispositivo().obter_dispositivos_de_usuario("5da64c50b22d0628e8533ea8")

    def test_obter_dispositivos_de_usuario_usuario_invalido(self):
        with self.assertRaises(UserDoesNotExist):
            Dispositivo().obter_dispositivos_de_usuario("14")

    def test_adicionar_dispositivo_sucesso(self):
        user = User(
            username="user",
            email="user@email.com",
            password="secret"
        ).save()

        Dispositivo().adicionar_dispostivo(
            user_id=user.id,
            uuid="123",
            token="---token---",
            name="nome",
            os="os"
        )

        self.assertEqual(
            User.objects(pk=user.id).first().devices,
            [UserDevice(
                id="123",
                token="---token---",
                active=True,
                name="nome",
                os="os"
            )]
        )

    def test_adicionar_dispositivo_usuario_inexistente(self):
        with self.assertRaises(UserDoesNotExist):
            Dispositivo().adicionar_dispostivo(
                user_id="inexistente",
                uuid="123",
                token="---token---",
                name="nome",
                os="os"
            )

    def test_adicionar_dispositivo_valores_invalidos(self):
        user = User(
            username="user",
            email="user@email.com",
            password="secret"
        ).save()

        with self.assertRaises(InvalidParametersError):
            Dispositivo().adicionar_dispostivo(
                user_id=user.id,
                uuid=True,
                token="---token---",
                active="olar",
                name="nome",
                os="os"
            )

    def test_adicionar_dispositivo_uuid_repetido(self):
        user = User(
            username="user",
            email="user@email.com",
            password="secret",
            devices=[UserDevice(
                id="123",
                token="---token---",
                active=True,
                name="nome",
                os="os"
            )]
        ).save()

        with self.assertRaises(InvalidParametersError):
            Dispositivo().adicionar_dispostivo(
                user_id=user.id,
                uuid="123",
                token="---token---",
                active=False,
                name="nome",
                os="os"
            )

    def test_atualizar_dispositivo_sucesso(self):
        device = UserDevice(
            id="14",
            token="---token---",
            name="Dispositivo",
            os="Android 14"
        )
        user = User(
            username="user",
            email="user@email.com",
            password="secret",
            devices=[device]
        ).save()

        Dispositivo().atualizar_dispositivo(user.id, device.id, active=False)

        self.assertEqual(
            User.objects(pk=user.id).first().devices,
            [UserDevice(
                id="14",
                token="---token---",
                active=False,
                name="Dispositivo",
                os="Android 14"
            )]
        )

    def test_atualizar_dispositivo_parametros_invalidos(self):
        device = UserDevice(
            id="14",
            token="---token---",
            name="Dispositivo",
            os="Android 14"
        )
        user = User(
            username="user",
            email="user@email.com",
            password="secret",
            devices=[device]
        ).save()

        Dispositivo().atualizar_dispositivo(user.id, device.id, nao_existo=True)

        self.assertEqual(
            User.objects(pk=user.id).first().devices,
            [UserDevice(
                id="14",
                token="---token---",
                name="Dispositivo",
                os="Android 14",
            )]
        )

    def test_apagar_dispositivo(self):
        device1 = UserDevice(
            id="1",
            token="---token1---",
            active=False,
            name="Dispositivo1",
            os="Android 14"
        )
        device2 = UserDevice(
            id="2",
            token="---token2---",
            name="Dispositivo2",
            os="Android 14"
        )
        user = User(
            username="user",
            email="user@email.com",
            password="secret",
            devices=[device1, device2]
        ).save()

        Dispositivo().apagar_dispositivo(user.id, device1.id)

        self.assertEqual(
            User.objects(pk=user.id).first().devices,
            [device2]
        )
