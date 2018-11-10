import json
import unittest
from unittest.mock import patch, call
from app import obter_relatorio
from flask import render_template

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

    @unittest.skip
    def test_obter_relatorio_json_inexistente_funcao_com_erro(self):
        #TODO
        #Pesquisar como mockar o render_template
        pass
