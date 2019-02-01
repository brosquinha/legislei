import json
import unittest
from unittest.mock import call, patch, ANY

from flask import render_template

from legislei.app import app
from legislei.cron import send_reports
from legislei.db import MongoDBClient
from legislei.exceptions import ModelError
from legislei.house_selector import obter_relatorio
from legislei.send_reports import send_email

customAssertionMsg = '{} differs from expected {}'

class TestMainAppMethods(unittest.TestCase):

    @patch("builtins.print")
    @patch("legislei.db.MongoDBClient.get_collection")
    def test_obter_relatorio_json_existente(
        self,
        mock_mongo_db,
        mock_print
    ):
        class FakeRelatorios:
            def find_one(self, obj):
                expected = {'idTemp': '123-hj'}
                if obj == expected:
                    return {'_id': 'TesteEmJson'}
                else:
                    raise AssertionError(customAssertionMsg.format(obj, expected))
        def func(**kwargs):
            pass
        mock_mongo_db.return_value = FakeRelatorios()
        
        actual_response = obter_relatorio('123', 'hj', func, periodo=7)

        self.assertEqual(actual_response, {'_id': 'TesteEmJson'})
        
    @patch("legislei.house_selector.house_selector")
    @patch("legislei.db.MongoDBClient.get_collection")
    def test_obter_relatorio_json_inexistente_funcao_sem_erro(
        self,
        mock_get_collection,
        mock_model_selector
    ):
        class FakeInsertOneResult:
            def __init__(self):
                self.inserted_id = 'Id'
        class FakeRelatorios:
            def find_one(self, obj):
                return None
            def insert_one(self, obj):
                expected = {
                    'nome': 'relatorio',
                    'idTemp': '123-hj'
                }
                if obj == expected:
                    return FakeInsertOneResult()
                raise AssertionError(customAssertionMsg.format(obj, expected))
        class FakeRelatorio:
            def to_dict(self):
                return {'nome': 'relatorio'}
        class FakeModel:
            def obter_relatorio(self, *args, **kwargs):
                return FakeRelatorio()
        mock_get_collection.return_value = FakeRelatorios()
        mock_model_selector.return_value = FakeModel

        actual_response = obter_relatorio('123', 'hj', 'modelTeste', periodo=7)

        self.assertEqual(actual_response, {'nome': 'relatorio', '_id': 'Id'})

    @patch("legislei.house_selector.house_selector")
    def test_obter_relatorio_json_inexistente_funcao_com_erro(
        self,
        mock_model_selector
    ):
        class FakeModel:
            def obter_relatorio(self, *args, **kwargs):
                raise ModelError('Erro')

        mock_model_selector.return_value = FakeModel

        with self.assertRaises(ModelError):
            obter_relatorio('123', 'hj', 'model', periodo=7)

    @patch("legislei.cron.send_email")
    @patch("legislei.cron.render_template")
    @patch("legislei.cron.obter_relatorio")
    def test_send_reports(
            self,
            mock_obter_relatorio,
            mock_render_template,
            mock_send_email
    ):
        mock_obter_relatorio.return_value = {"nice": "JSON"}
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

        self.assertEqual(mock_obter_relatorio.call_count, 3)
        self.assertEqual(mock_render_template.call_count, 1)
        mock_send_email.assert_called_once_with("test@test.com", "<html>Nice</html>")

    @patch("legislei.cron.send_email")
    @patch("legislei.cron.render_template")
    @patch("legislei.cron.obter_relatorio")
    def test_send_reports_one_obter_relatorio_fails(
        self,
        mock_obter_relatorio,
        mock_render_template,
        mock_send_email
    ):
        def fake_obter_relatorio(parlamentar, *args, **kwargs):
            if parlamentar == 2:
                raise ModelError('msg')
            return {"nice": "JSON"}
        mock_obter_relatorio.side_effect = fake_obter_relatorio
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

        self.assertEqual(mock_obter_relatorio.call_count, 3)
        self.assertEqual(mock_render_template.call_count, 1)
        mock_send_email.assert_called_once_with("test@test.com", "<html>Nice</html>")
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
