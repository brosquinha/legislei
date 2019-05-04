import json
import unittest
from datetime import datetime
from unittest.mock import ANY, call, patch

from flask import render_template
from mongoengine import connect

from legislei.cron import send_reports
from legislei.exceptions import ModelError
from legislei.house_selector import obter_relatorio
from legislei.models.relatorio import Parlamentar, Relatorio
from legislei.send_reports import send_email

customAssertionMsg = '{} differs from expected {}'


class TestCron(unittest.TestCase):

    def setUp(self):
        connect('mongoenginetest', host='mongomock://localhost')

    def tearDown(self):
        Relatorio.drop_collection()
    
    @patch("legislei.cron.send_email")
    @patch("legislei.cron.render_template")
    def test_send_reports(
            self,
            mock_render_template,
            mock_send_email
    ):
        agora = datetime.now()
        data_final = datetime(agora.year, agora.month, agora.day)
        parlamentar1 = Parlamentar(id='1', cargo='BR1')
        parlamentar2 = Parlamentar(id='2', cargo='BR2')
        parlamentar3 = Parlamentar(id='3', cargo='BR1')
        Relatorio(parlamentar=parlamentar1, data_final=data_final).save()
        Relatorio(parlamentar=parlamentar2, data_final=data_final).save()
        Relatorio(parlamentar=parlamentar3, data_final=data_final).save()
        mock_render_template.return_value = "<html>Nice</html>"
        mock_send_email.return_value = True

        data = [
            {
                "parlamentares": [
                    {
                        'id': '1',
                        'cargo': 'BR1'
                    },
                    {
                        'id': '2',
                        'cargo': 'BR2'
                    },
                    {
                        'id': '3',
                        'cargo': 'BR1'
                    }
                ],
                "intervalo": 7,
                "email": "test@test.com"
            }
        ]
        send_reports(data)

        self.assertEqual(mock_render_template.call_count, 1)
        mock_send_email.assert_called_once_with(
            "test@test.com", "<html>Nice</html>")

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
                if parlamentar == 2:
                    raise ModelError('msg')
                return {"nice": "JSON"}
        mock_Relatorios.side_effect = FakeRelatorios
        mock_render_template.return_value = "<html>Nice</html>"
        mock_send_email.return_value = True

        data = [
            {
                "parlamentares": [
                    {
                        'id': 1,
                        'cargo': 'BR1'
                    },
                    {
                        'id': 2,
                        'cargo': 'SP'
                    },
                    {
                        'id': 3,
                        'cargo': 'BR1'
                    }
                ],
                "intervalo": 7,
                "email": "test@test.com"
            }
        ]
        send_reports(data)

        self.assertEqual(mock_Relatorios.call_count, 3)
        self.assertEqual(mock_render_template.call_count, 1)
        mock_send_email.assert_called_once_with(
            "test@test.com", "<html>Nice</html>")
        mock_render_template.assert_called_once_with(
            'relatorio_deputado_email.out.html',
            relatorios=[
                {"nice": "JSON"},
                {
                    'parlamentar': {
                        'id': 2,
                        'cargo': 'SP'
                    },
                    'eventosPresentes': None,
                    'eventosPrevistos': None,
                    'proposicoes': None
                },
                {"nice": "JSON"},
            ],
            data_inicial=ANY,
            data_final=ANY,
            data_final_link=ANY,
            intervalo=7,
            host=ANY
        )
