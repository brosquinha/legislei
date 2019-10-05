import json
import logging
import unittest
from datetime import datetime, timedelta
from unittest.mock import ANY, call, patch

import pytz
from flask import render_template
from mongoengine import connect

logging.disable(logging.CRITICAL)

from legislei.cron import send_reports
from legislei.exceptions import ModelError
from legislei.house_selector import obter_relatorio
from legislei.models.inscricoes import Inscricoes
from legislei.models.relatorio import Parlamentar, Relatorio
from legislei.models.user import User
from legislei.send_reports import send_email


customAssertionMsg = '{} differs from expected {}'


class TestCron(unittest.TestCase):

    def setUp(self):
        connect('mongoenginetest', host='mongomock://localhost')
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        Relatorio.drop_collection()
        logging.disable(logging.NOTSET)
    
    @patch("legislei.cron.send_email")
    @patch("legislei.cron.render_template")
    def test_send_reports_multiplos_parlamentares(
            self,
            mock_render_template,
            mock_send_email
    ):
        brasilia_tz = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now()
        data_final = datetime(agora.year, agora.month, agora.day)
        data_final = brasilia_tz.localize(data_final)
        data_inicial = data_final - timedelta(days=7)
        parlamentar1 = Parlamentar(id='1', cargo='BR1')
        parlamentar2 = Parlamentar(id='2', cargo='BR2')
        parlamentar3 = Parlamentar(id='3', cargo='BR1')
        Relatorio(
            parlamentar=parlamentar1,
            data_final=data_final,
            data_inicial=data_inicial
        ).save()
        Relatorio(
            parlamentar=parlamentar2,
            data_final=data_final,
            data_inicial=data_inicial
        ).save()
        Relatorio(
            parlamentar=parlamentar3,
            data_final=data_final,
            data_inicial=data_inicial
        ).save()
        mock_render_template.return_value = "<html>Nice</html>"
        mock_send_email.return_value = True
        user = [User(
            username='user',
            password='pwd',
            email='test@test.com',
            inscricoes=Inscricoes(
                parlamentares=[parlamentar1, parlamentar2, parlamentar3],
                intervalo=7
            )
        )]

        send_reports(user, data_final=agora)

        self.assertEqual(mock_render_template.call_count, 1)
        mock_send_email.assert_called_once_with(
            "test@test.com", "<html>Nice</html>")

    def _test_send_reports_multiplos_intervalos(
        self,
        agora,
        mock_render_template,
        mock_send_email
    ):
        brasilia_tz = pytz.timezone('America/Sao_Paulo')
        data_final = datetime(agora.year, agora.month, agora.day)
        data_final = brasilia_tz.localize(data_final)
        parlamentar1 = Parlamentar(id='1', cargo='BR1')
        Relatorio(
            parlamentar=parlamentar1,
            data_final=data_final,
            data_inicial=data_final - timedelta(days=7)
        ).save()
        Relatorio(
            parlamentar=parlamentar1,
            data_final=data_final,
            data_inicial=data_final - timedelta(days=14)
        ).save()
        Relatorio(
            parlamentar=parlamentar1,
            data_final=data_final,
            data_inicial=data_final - timedelta(days=28)
        ).save()
        mock_render_template.return_value = "<html>Nice</html>"
        mock_send_email.return_value = True
        users = [
            User(
                username='user1',
                password='pwd',
                email='test1@test.com',
                inscricoes=Inscricoes(
                    parlamentares=[parlamentar1],
                    intervalo=7
                )
            ),
            User(
                username='user2',
                password='pwd',
                email='test2@test.com',
                inscricoes=Inscricoes(
                    parlamentares=[parlamentar1],
                    intervalo=14
                )
            ),
            User(
                username='user4',
                password='pwd',
                email='test4@test.com',
                inscricoes=Inscricoes(
                    parlamentares=[parlamentar1],
                    intervalo=28
                )
            )
        ]

        send_reports(users, data_final=agora)
    
    @patch("legislei.cron.send_email")
    @patch("legislei.cron.render_template")
    def test_send_reports_multiplos_intervalos_sem_4_semanas(
            self,
            mock_render_template,
            mock_send_email
    ):
        self._test_send_reports_multiplos_intervalos(
            agora=datetime(2019, 6, 29),
            mock_render_template=mock_render_template,
            mock_send_email=mock_send_email
        )

        self.assertEqual(mock_render_template.call_count, 2)
        self.assertEqual(mock_send_email.call_count, 2)
        mock_send_email.assert_has_calls(
            [
                call("test1@test.com", "<html>Nice</html>"),
                call("test2@test.com", "<html>Nice</html>")
            ]
        )

    @patch("legislei.cron.send_email")
    @patch("legislei.cron.render_template")
    def test_send_reports_multiplos_intervalos_com_4_semanas(
            self,
            mock_render_template,
            mock_send_email
    ):
        self._test_send_reports_multiplos_intervalos(
            agora=datetime(2019, 6, 15),
            mock_render_template=mock_render_template,
            mock_send_email=mock_send_email
        )

        self.assertEqual(mock_render_template.call_count, 3)
        self.assertEqual(mock_send_email.call_count, 3)
        mock_send_email.assert_has_calls(
            [
                call("test1@test.com", "<html>Nice</html>"),
                call("test2@test.com", "<html>Nice</html>"),
                call("test4@test.com", "<html>Nice</html>")
            ]
        )

    @patch("legislei.cron.send_email")
    @patch("legislei.cron.render_template")
    def test_send_reports_multiplos_intervalos_semana_impar(
            self,
            mock_render_template,
            mock_send_email
    ):
        self._test_send_reports_multiplos_intervalos(
            agora=datetime(2019, 6, 8),
            mock_render_template=mock_render_template,
            mock_send_email=mock_send_email
        )

        self.assertEqual(mock_render_template.call_count, 1)
        self.assertEqual(mock_send_email.call_count, 1)
        mock_send_email.assert_has_calls(
            [
                call("test1@test.com", "<html>Nice</html>")
            ]
        )
    
    @patch("legislei.cron.send_email")
    @patch("legislei.cron.render_template")
    @patch("legislei.cron.Relatorios")
    def test_send_reports_one_obter_relatorio_fails(
        self,
        mock_Relatorios,
        mock_render_template,
        mock_send_email
    ):
        class FakeRelatorios():
            def obter_relatorio(self, parlamentar, *args, **kwargs):
                if parlamentar == '2':
                    raise ModelError('msg')
                return {"nice": "JSON"}
        mock_Relatorios.side_effect = FakeRelatorios
        mock_render_template.return_value = "<html>Nice</html>"
        mock_send_email.return_value = True
        parlamentar1 = Parlamentar(id='1', cargo='BR1')
        parlamentar2 = Parlamentar(id='2', cargo='BR2')
        parlamentar3 = Parlamentar(id='3', cargo='BR1')
        user = [User(
            username='user',
            password='pwd',
            email='test@test.com',
            inscricoes=Inscricoes(
                parlamentares=[parlamentar1, parlamentar2, parlamentar3],
                intervalo=7
            )
        )]

        send_reports(user)

        self.assertEqual(mock_Relatorios.call_count, 3)
        self.assertEqual(mock_render_template.call_count, 1)
        mock_send_email.assert_called_once_with(
            "test@test.com", "<html>Nice</html>")
        mock_render_template.assert_called_once_with(
            'relatorio_deputado_email.out.html',
            relatorios=[
                {"nice": "JSON"},
                {
                    'parlamentar': parlamentar2,
                    'eventosPresentes': None,
                    'eventosPrevistos': None,
                    'proposicoes': None,
                    '_id': None
                },
                {"nice": "JSON"},
            ],
            data_inicial=ANY,
            data_final=ANY,
            host=ANY
        )
