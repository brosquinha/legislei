import json
import logging
import smtplib
import unittest
from datetime import datetime
from unittest.mock import patch

from legislei.models.relatorio import (Evento, Parlamentar, Proposicao,
                                       Relatorio)
from legislei.send_reports import send_email, send_push_notification, uses_ssl


class TestSendReports(unittest.TestCase):

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)
    
    @patch("smtplib.SMTP_SSL" if uses_ssl else "smtplib.SMTP")
    @patch("legislei.send_reports.MIMEText")
    def test_send_email(
            self,
            mock_MIMEText,
            mock_SMTP
    ):
        data_inicial = datetime(2019, 10, 12)
        data_final = datetime(2019, 10, 19)
        parlamentar1 = Parlamentar(id='1', cargo='BR1', nome='AMANDA')
        parlamentar2 = Parlamentar(id='2', cargo='BR2', nome='SANTOS')
        parlamentar3 = Parlamentar(id='3', cargo='BR1', nome='FULANO')
        relatorio1 = Relatorio(
            parlamentar=parlamentar1,
            data_final=data_final,
            data_inicial=data_inicial
        )
        relatorio2 = Relatorio(
            parlamentar=parlamentar2,
            data_final=data_final,
            data_inicial=data_inicial
        )
        relatorio3 = Relatorio(
            parlamentar=parlamentar3,
            data_final=data_final,
            data_inicial=data_inicial
        )
        #Não consegui nem encontrei como mockar Header e MIMEText...
        def assert_in(member, container):
            return self.assertIn(member, container)
        class FakeMIMEText():
            def __init__(self, html, *args, **kwargs):
                assert_in("AMANDA", html)
                assert_in("FULANO", html)
                assert_in("SANTOS", html)
                assert_in("12/10/2019", html)
                assert_in("19/10/2019", html)
            def __setitem__(self, name, value):
                pass
            def as_string(self):
                return 'ok'
        
        class FakeSMTP():
            def __init__(self, *args, **kwargs):
                pass
            def starttls(self):
                self.starttls_called = True
            def ehlo(self):
                pass
            def login(self, *args):
                self.login_args = args
            def sendmail(self, *args):
                self.sendmail_args = args
            def quit(self):
                self.quit_called = True

        mock_SMTP.side_effect = FakeSMTP
        mock_MIMEText.side_effect = FakeMIMEText

        send_email(
            email="test@test.com",
            reports=[relatorio1, relatorio2, relatorio3],
            dates=(data_inicial, data_final)
        )

        self.assertEqual(1, mock_SMTP.call_count)

    @patch("legislei.send_reports.urllib3.PoolManager")
    def test_send_push_notification(self, mock_urllib3):
        def assert_equal(actual, expected):
            self.assertEqual(actual, expected)
        data_inicial = datetime(2019, 10, 12)
        data_final = datetime(2019, 10, 19)
        parlamentar1 = Parlamentar(id='1', cargo='BR1', nome='AMANDA')
        relatorio1 = Relatorio(
            id="123",
            parlamentar=parlamentar1,
            data_final=data_final,
            data_inicial=data_inicial,
            proposicoes=[
                Proposicao(id="1"), Proposicao(id="2"), Proposicao(id="3"), Proposicao(id="4")],
            eventos_presentes=[Evento(id="1"), Evento(id="2")],
            eventos_previstos=None,
            eventos_ausentes=[Evento(id="4"), Evento(id="5"), Evento(id="6")]
        )
        expected_reports = [{
            "_id": "123",
            "parlamentar": parlamentar1.to_dict(),
            "mensagem": None,
            "dataInicial": str(data_inicial),
            "dataFinal": str(data_final),
            "orgaos": 0,
            "proposicoes": 4,
            "eventosPresentes": 2,
            "eventosAusentes": 3,
            "eventosPrevistos": 0,
            "presencaRelativa": "100.00%",
            "presencaTotal": "40.00%",
            "eventosAusentesEsperadosTotal": 0
        }]
        class FakePoolManager:
            def __init__(self, *args, **kwargs):
                pass
            def request(self, method, url, headers, body):
                assert_equal(method, "POST")
                assert_equal(url, "https://fcm.googleapis.com/fcm/send")
                assert_equal(json.loads(body.decode('utf-8'))["data"]["reports"], expected_reports)
        mock_urllib3.side_effect = FakePoolManager

        send_push_notification("token", [relatorio1.to_dict()])

        self.assertTrue(mock_urllib3.called)
