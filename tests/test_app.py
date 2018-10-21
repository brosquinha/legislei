import json
import unittest
from unittest.mock import patch
from SDKs.CamaraDeputados.entidades import Deputados, Eventos, Proposicoes, Votacoes
from app import obterDeputados, dep

class TestMainAppMethods(unittest.TestCase):

    @patch("app.dep.obterTodosDeputados")
    def test_obterDeputados(self, mock_obterTodosDeputados):
        def fakeObterDeputados():
            yield [{'nome': 'CESAR DA SILVA'}, {'nome': 'FULANO PESSOA'}]
            yield [{'nome': 'SICRANO PINTO'}]
        mock_obterTodosDeputados.side_effect = fakeObterDeputados
        actual_response = obterDeputados()
        mock_obterTodosDeputados.assert_any_call()
        self.assertEqual(actual_response[0], json.dumps([
            {'nome': 'CESAR DA SILVA'},
            {'nome': 'FULANO PESSOA'},
            {'nome': 'SICRANO PINTO'}
        ]))
