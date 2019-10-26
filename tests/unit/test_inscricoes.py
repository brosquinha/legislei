import logging
import unittest
import warnings
from datetime import datetime
from unittest.mock import patch

from mongoengine import connect

from legislei.exceptions import UserDoesNotExist
from legislei.models.inscricoes import Inscricoes
from legislei.models.relatorio import Parlamentar
from legislei.models.user import User
from legislei.services.inscricoes import Inscricao


class TestInscricao(unittest.TestCase):
    
    def setUp(self):
        logging.disable(logging.CRITICAL)
        connect('mongoenginetest', host='mongomock://localhost')
        self.parlamentar1 = Parlamentar(id='id', cargo='BR1')
        self.parlamentar2 = Parlamentar(id='id', cargo='BR2')
        self.parlamentar3 = Parlamentar(id='di', cargo='BR1')

    def tearDown(self):
        User.drop_collection()

    def _prepare_tests_obter_todas_inscricoes_para_processar(self):
        inscricoes1 = Inscricoes(
            intervalo=7,
            parlamentares=[self.parlamentar1, self.parlamentar2]
        )
        inscricoes2 = Inscricoes(
            intervalo=14,
            parlamentares=[self.parlamentar1]
        )
        inscricoes3 = Inscricoes(
            intervalo=7,
            parlamentares=[]
        )
        inscricoes4 = Inscricoes(
            intervalo=28,
            parlamentares=[self.parlamentar3]
        )
        self.user1 = User(
            username='user1',
            password='pwd',
            email='user1@email.com',
            inscricoes=inscricoes1
        )
        self.user1.save()
        self.user2 = User(
            username='user2',
            password='pwd',
            email='user2@email.com',
            inscricoes=inscricoes2
        )
        self.user2.save()
        self.user3 = User(
            username='user3',
            password='pwd',
            email='user3@email.com',
            inscricoes=inscricoes3
        )
        self.user3.save()
        self.user4 = User(
            username='user4',
            password='pwd',
            email='user4@email.com',
            inscricoes=inscricoes4
        )
        self.user4.save()
        self.user5 = User(
            username='user5',
            password='pwd',
            email='user5@email.com'
        ).save()
    
    def test_obter_todas_inscricoes_para_processar_semana_par(self):
        data_final = datetime(2019, 10, 19)
        self._prepare_tests_obter_todas_inscricoes_para_processar()

        actual = Inscricao().obter_todas_inscricoes_para_processar(data_final=data_final)

        self.assertEqual(actual, [self.user1, self.user2])

    def test_obter_todas_inscricoes_para_processar_semana_impar(self):
        data_final = datetime(2019, 10, 12)
        self._prepare_tests_obter_todas_inscricoes_para_processar()

        actual = Inscricao().obter_todas_inscricoes_para_processar(data_final=data_final)

        self.assertEqual(actual, [self.user1])

    def test_obter_todas_inscricoes_para_processar_semana_de_mes(self):
        data_final = datetime(2019, 11, 2)
        self._prepare_tests_obter_todas_inscricoes_para_processar()

        actual = Inscricao().obter_todas_inscricoes_para_processar(data_final=data_final)

        self.assertEqual(actual, [self.user1, self.user2, self.user4])

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

    @patch("legislei.services.inscricoes.obter_parlamentar")
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

    @patch("legislei.services.inscricoes.obter_parlamentar")
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
