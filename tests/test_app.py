import json
import unittest
from unittest.mock import patch, call
from app import obter_relatorio, send_reports, send_email, app
from flask import render_template
from exceptions import ModelError

class TestMainAppMethods(unittest.TestCase):

    @patch("builtins.print")
    @patch("builtins.open")
    @patch("json.loads")
    def test_obter_relatorio_json_existente(
        self,
        mock_json_loads,
        mock_open,
        mock_print
    ):
        class FakeOpen:
            def __init__(self, *args, **kwargs):
                pass
            def read(self):
                return 'Teste'
        def func(**kwargs):
            pass
        mock_open.side_effect = FakeOpen
        mock_json_loads.return_value = 'TesteEmJson'
        
        actual_response = obter_relatorio('123', 'hj', func)

        mock_json_loads.assert_called_once_with('Teste')
        mock_open.assert_called_once_with('reports/123-hj.json')
        self.assertEqual(actual_response, 'TesteEmJson')
        
    @patch("builtins.open")
    @patch("json.dumps")
    def test_obter_relatorio_json_inexistente_funcao_sem_erro(
        self,
        mock_json_dumps,
        mock_open
    ):
        class FakeOpen:
            def __init__(self, file, mode=None):
                if mode == None:
                    raise FileNotFoundError()
            def write(self, *args):
                pass
            def close(self):
                pass
        def func(*args, **kwargs):
            return 'relatorio'
        mock_open.side_effect = FakeOpen
        mock_json_dumps.return_value = 'jsonstr'

        actual_response = obter_relatorio('123', 'hj', func)

        mock_json_dumps.assert_called_once_with('relatorio')
        mock_open.assert_has_calls([
            call('reports/123-hj.json'),
            call('reports/123-hj.json', 'w+')])
        self.assertEqual(actual_response, 'relatorio')

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
            actual_response = obter_relatorio('123', 'hj', func)
        
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

        data = {
            "lista": [
                {
                    "parlamentares": [1, 2, 3],
                    "intervalo": 7,
                    "email": "test@test.com"
                }
            ]
        }
        send_reports(data)

        self.assertEqual(mock_obter_relatorio.call_count, 3)
        self.assertEqual(mock_render_template.call_count, 1)
        mock_send_email.assert_called_once_with("test@test.com", "<html>Nice</html>")
