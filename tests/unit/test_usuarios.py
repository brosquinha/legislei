import unittest
from unittest.mock import patch

from mongoengine import connect

from legislei.exceptions import (InvalidEmail, RequirementsNotMet,
                                 UsernameOrEmailAlreadyExistis)
from legislei.models.user import User
from legislei.services.usuarios import Usuario


class TestUsuario(unittest.TestCase):

    def setUp(self):
        connect('mongoenginetest', host='mongomock://localhost')

    def tearDown(self):
        User.drop_collection()

    def test_obter_por_id(self):
        user = User(
            username='user',
            password='pwd',
            email='test@email.com'
        )
        user.save()

        actual = Usuario().obter_por_id(user.pk)

        self.assertEqual(actual, user)

    def test_registrar_sucesso(self):
        Usuario().registrar('user', '1234', '1234', 'test@email.com')

        expected = User.objects(username='user').first()
        self.assertEqual(expected.email, 'test@email.com')

    def test_registrar_user_ja_existe(self):
        user = User(
            username='user',
            password='pwd',
            email='test@email.com'
        )
        user.save()

        with self.assertRaises(UsernameOrEmailAlreadyExistis):
            Usuario().registrar('user', '1234', '1234', 'test2@email.com')

    def test_registrar_email_ja_existe(self):
        user = User(
            username='user',
            password='pwd',
            email='test@email.com'
        )
        user.save()

        with self.assertRaises(UsernameOrEmailAlreadyExistis):
            Usuario().registrar('user2', '1234', '1234', 'test@email.com')

    def test_registrar_email_invalido(self):
        user = User(
            username='user',
            password='pwd',
            email='test@email.com'
        )
        user.save()

        with self.assertRaises(InvalidEmail):
            Usuario().registrar('user2', '1234', '1234', 'invalid-email')

    def test_registrar_senhas_diferentes(self):
        user = User(
            username='user',
            password='pwd',
            email='test@email.com'
        )
        user.save()

        with self.assertRaises(RequirementsNotMet):
            Usuario().registrar('user2', '1234', '4321', 'test2@email.com')

    def test_registrar_username_mto_curto(self):
        user = User(
            username='user',
            password='pwd',
            email='test@email.com'
        )
        user.save()

        with self.assertRaises(RequirementsNotMet):
            Usuario().registrar('u', '1234', '1234', 'test2@email.com')

    @patch("legislei.services.usuarios.login_user")
    def test_login_sucesso(self, mock_login):
        user = User(
            username='user',
            password='$pbkdf2-sha256$16$916rFQLgXItR6n0v5fz/3w$k1XO4U9rRqZjZ5YAfNi2f8vGmzwXLcuSWMbt/yYYFAU',
            email='test@email.com'
        )
        user.save()

        actual = Usuario().login('user', '1234', True)

        self.assertTrue(actual)
        mock_login.assert_called_once_with(user, remember=True)

    def test_login_senha_errada(self):
        user = User(
            username='user',
            password='$pbkdf2-sha256$16$916rFQLgXItR6n0v5fz/3w$k1XO4U9rRqZjZ5YAfNi2f8vGmzwXLcuSWMbt/yYYFAU',
            email='test@email.com'
        )
        user.save()

        actual = Usuario().login('user', '4321', True)

        self.assertFalse(actual)

    def test_login_usuario_nao_existe(self):
        user = User(
            username='user',
            password='pwd',
            email='test@email.com'
        )
        user.save()

        actual = Usuario().login('inexistente', '4321', True)

        self.assertFalse(actual)

    @patch("legislei.services.usuarios.logout_user")
    def test_logout(self, mock_logout):
        Usuario().logout()
        
        mock_logout.assert_called_once_with()
