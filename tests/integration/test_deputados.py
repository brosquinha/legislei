import json
import unittest
import warnings
from datetime import date
from unittest.mock import patch

from legislei.models.deputados import DeputadosApp


class TestDeputados(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter("ignore")
    
    @patch("builtins.print")
    def test_obter_relatorio(self, mock_print):
        parlamentar = json.loads("""{
            "cargo" : "BR1",
            "uf" : "RJ",
            "partido" : "PSOL",
            "foto" : "http://www.camara.leg.br/internet/deputado/bandep/74171.jpg",
            "nome" : "CHICO ALENCAR",
            "id" : "74171"
        }""")
        actual = DeputadosApp().obter_relatorio(
            "74171",
            "2018-06-29",
            7
        ).to_dict()
        self.maxDiff = None
        self.assertDictEqual(actual["parlamentar"], parlamentar)
        self.assertEqual(len(actual["eventosAusentes"]), 53)
        self.assertEqual(len(actual["eventosPrevistos"]), 9)
        self.assertEqual(len(actual["eventosPresentes"]), 5)
        self.assertEqual(len(actual["proposicoes"]), 4)
        self.assertEqual(len(actual["orgaos"]), 17)
        self.assertEqual(actual["dataFinal"], "29/06/2018")
        self.assertEqual(actual["eventosAusentesEsperadosTotal"], 9)
        self.assertEqual(actual["presencaTotal"], "9.43%")
        self.assertEqual(actual["presencaRelativa"], "55.56%")
        self.assertEqual(actual["dataInicial"], "22/06/2018")

    def test_obter_parlamentares(self):
        expected = 512
        actual = DeputadosApp().obter_parlamentares()
        self.assertEqual(len(actual), expected)

    def test_obter_parlamentar(self):
        expected = json.loads("""{
            "cargo" : "BR1",
            "uf" : "RJ",
            "partido" : "PSOL",
            "foto" : "http://www.camara.leg.br/internet/deputado/bandep/74171.jpg",
            "nome" : "CHICO ALENCAR",
            "id" : "74171"
        }""")
        actual = DeputadosApp().obter_parlamentar("74171").to_dict()
        self.assertDictEqual(actual, expected)
