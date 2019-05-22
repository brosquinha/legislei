import unittest
import warnings
from unittest.mock import patch

from mongoengine import connect

from legislei.exceptions import UserDoesNotExist
from legislei.inscricoes import Inscricao
from legislei.models.inscricoes import Inscricoes
from legislei.models.relatorio import Parlamentar
from legislei.models.user import User

class TestInscricao(unittest.TestCase):
    
    def setUp(self):
        connect('mongoenginetest', host='mongomock://localhost')
        self.parlamentar1 = Parlamentar(id='id', cargo='BR1')
        self.parlamentar2 = Parlamentar(id='id', cargo='BR2')

    def tearDown(self):
        User.drop_collection()

    def test_obter_todas_inscricoes(self):
        inscricoes1 = Inscricoes(
            intervalo=7,
            parlamentares=[self.parlamentar1, self.parlamentar2]
        )
        inscricoes2 = Inscricoes(
            intervalo=7,
            parlamentares=[self.parlamentar1]
        )
        User(
            username='user1',
            password='pwd',
            email='user1@email.com',
            inscricoes=inscricoes1
        ).save()
        User(
            username='user2',
            password='pwd',
            email='user2@email.com',
            inscricoes=inscricoes2
        ).save()

        actual = Inscricao().obter_todas_inscricoes()

        self.assertEqual(actual, [inscricoes1, inscricoes2])

    def test_obter_minhas_inscricoes_com_inscricoes(self):
        inscricoes = Inscricoes(
            intervalo=14,
            parlamentares=[self.parlamentar1, self.parlamentar2]
        )
        User(
            username='user',
            password='pwd',
            email='test@email.com',
            inscricoes=inscricoes
        ).save()

        actual = Inscricao().obter_minhas_inscricoes('test@email.com')

        self.assertEqual(actual[0], [self.parlamentar1, self.parlamentar2])
        self.assertEqual(actual[1], 14)

    def test_obter_minhas_inscricoes_nenhuma_inscricao(self):
        User(
            username='user',
            password='pwd',
            email='test@email.com'
        ).save()

        actual = Inscricao().obter_minhas_inscricoes('test@email.com')

        self.assertEqual(actual[0], [])
        self.assertEqual(actual[1], 7)

    def test_obter_minhas_inscricoes_user_doesnt_exist(self):
        with self.assertRaises(UserDoesNotExist):
            Inscricao().obter_minhas_inscricoes('test@email.com')

    @patch("legislei.inscricoes.obter_parlamentar")
    def test_nova_inscricao_primeira_inscricao(self, mock_obter_parlamentar):
        warnings.simplefilter("ignore")
        mock_obter_parlamentar.return_value = self.parlamentar1
        User(
            username='user',
            password='pwd',
            email='test@email.com'
        ).save()

        Inscricao().nova_inscricao(
            self.parlamentar1.cargo,
            self.parlamentar1.id,
            'test@email.com'
        )

        self.assertEqual(
            User.objects(username='user').first().inscricoes,
            Inscricoes(
                intervalo=7,
                parlamentares=[self.parlamentar1]
            )
        )

    @patch("legislei.inscricoes.obter_parlamentar")
    def test_nova_inscricao_outra_inscricao(self, mock_obter_parlamentar):
        warnings.simplefilter("ignore")
        mock_obter_parlamentar.return_value = self.parlamentar1
        User(
            username='user',
            password='pwd',
            email='test@email.com',
            inscricoes=Inscricoes(
                intervalo=14,
                parlamentares=[self.parlamentar2]
            )
        ).save()

        Inscricao().nova_inscricao(
            self.parlamentar1.cargo,
            self.parlamentar1.id,
            'test@email.com'
        )

        self.assertEqual(
            User.objects(username='user').first().inscricoes,
            Inscricoes(
                intervalo=14,
                parlamentares=[self.parlamentar2, self.parlamentar1]
            )
        )

    def test_nova_inscricao_user_doesnt_exist(self):
        with self.assertRaises(UserDoesNotExist):
            Inscricao().nova_inscricao(
                self.parlamentar1.cargo,
                self.parlamentar1.id,
                'test@email.com'
            )

    def test_remover_inscricao(self):
        User(
            username='user',
            password='pwd',
            email='test@email.com',
            inscricoes=Inscricoes(
                intervalo=14,
                parlamentares=[self.parlamentar2]
            )
        ).save()

        Inscricao().remover_inscricao(
            self.parlamentar2.cargo,
            self.parlamentar2.id,
            'test@email.com'
        )

        self.assertEqual(
            User.objects(username='user').first().inscricoes,
            Inscricoes(intervalo=14, parlamentares=[])
        )

    def test_alterar_configs_valida(self):
        User(
            username='user',
            password='pwd',
            email='test@email.com',
            inscricoes=Inscricoes(
                intervalo=7,
                parlamentares=[]
            )
        ).save()

        Inscricao().alterar_configs(21, 'test@email.com')

        self.assertEqual(
            User.objects(username='user').first().inscricoes.intervalo,
            21
        )

    def test_alterar_configs_invalida(self):
        User(
            username='user',
            password='pwd',
            email='test@email.com',
            inscricoes=Inscricoes(
                intervalo=7,
                parlamentares=[]
            )
        ).save()

        Inscricao().alterar_configs(30, 'test@email.com')

        self.assertEqual(
            User.objects(username='user').first().inscricoes.intervalo,
            7
        )
