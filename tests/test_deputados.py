import json
import unittest
from unittest.mock import patch
from SDKs.CamaraDeputados.entidades import Deputados
from deputados import DeputadosApp

class TestDeputadosApp(unittest.TestCase):

    @patch("SDKs.CamaraDeputados.entidades.Deputados.obterTodosDeputados")
    def test_obterDeputados(self, mock_obterTodosDeputados):
        def fakeObterDeputados():
            yield [{'nome': 'CESAR DA SILVA'}, {'nome': 'FULANO PESSOA'}]
            yield [{'nome': 'SICRANO PINTO'}]
        mock_obterTodosDeputados.side_effect = fakeObterDeputados
        dep = DeputadosApp()
        actual_response = dep.obterDeputados()
        mock_obterTodosDeputados.assert_any_call()
        self.assertEqual(actual_response[0], json.dumps([
            {'nome': 'CESAR DA SILVA'},
            {'nome': 'FULANO PESSOA'},
            {'nome': 'SICRANO PINTO'}
        ]))