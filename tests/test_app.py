import json
import unittest
from unittest.mock import patch, call
from app import obter_relatorio, send_reports, send_email, app
from flask import render_template
from exceptions import ModelError
from db import MongoDBClient

customAssertionMsg = '{} differs from expected {}'

class TestMainAppMethods(unittest.TestCase):

    @patch("builtins.print")
    @patch("db.MongoDBClient.get_collection")
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
        
    @patch("db.MongoDBClient.get_collection")
    def test_obter_relatorio_json_inexistente_funcao_sem_erro(
        self,
        mock_get_collection
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
        def func(*args, **kwargs):
            return FakeRelatorio()
        mock_get_collection.return_value = FakeRelatorios()

        actual_response = obter_relatorio('123', 'hj', func, periodo=7)

        self.assertEqual(actual_response, {'nome': 'relatorio', '_id': 'Id'})

    @patch("builtins.open")
    @patch("app.render_template")
    def test_obter_relatorio_json_inexistente_funcao_com_erro(
        self,
        mock_render_template,
        mock_open
    ):
        class FakeOpen:
            def __init__(self, file, mode=None):
                raise FileNotFoundError()
            def write(self, *args):
                pass
            def close(self):
                pass
        def func(*args, **kwargs):
            raise ModelError("Erro")

        mock_open.side_effect = FakeOpen
        mock_render_template.return_value = True

        with app.app_context():
            actual_response = obter_relatorio('123', 'hj', func, periodo=7)
        
        self.assertEqual(actual_response, (True, 500))
        mock_render_template.assert_called_once_with(
            'erro.html',
            erro_titulo='500 - Serviço indisponível',
            erro_descricao="Erro"
        )

    @patch("app.send_email")
    @patch("app.render_template")
    @patch("app.obter_relatorio")
    @patch("models.deputados.DeputadosApp")
    def test_send_reports(
            self,
            mock_deputadosApp,
            mock_obter_relatorio,
            mock_render_template,
            mock_send_email
        ):
        class FakeDeputadosApp():
            def consultar_deputado(self, *args, **kwargs):
                return {}

        mock_deputadosApp.side_effect = FakeDeputadosApp
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
