import json
import unittest
from unittest.mock import patch
from app import obterDeputados, DeputadosApp

class TestMainAppMethods(unittest.TestCase):

    @patch("app.DeputadosApp.obterDeputados")
    def test_obterDeputados(self, mock_obterDeputados):
        obterDeputados()
        mock_obterDeputados.assert_any_call()
