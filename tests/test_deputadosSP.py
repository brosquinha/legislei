import unittest
from unittest.mock import patch
from models.deputadosSP import DeputadosALESPApp

class TestDeputadosSPApp(unittest.TestCase):

    def setUp(self):
        self.dep = DeputadosALESPApp()

    @patch("SDKs.AssembleiaLegislativaSP.deputados.Deputados.obterTodosDeputados")
    def test_obterDeputado(self, mock_obterTodosDeputados):
        mock_obterTodosDeputados.return_value = [
            {'id': '12'},
            {'id': '11'},
            {'id': '14', 'nome': 'Teste'},
        ]

        actual_response = self.dep.obterDeputado('14')

        self.assertEqual({'id': '14', 'nome': 'Teste'}, actual_response)
