import json
import unittest
import warnings
from unittest.mock import patch

from legislei.houses.alesp import ALESPHandler


class TestALESPHandlerIntegration(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter("ignore")
    
    @patch("builtins.print")
    def test_obter_relatorio(self, mock_print):
        parlamentar = json.loads("""{
            "cargo" : "SP",
            "uf" : "SP",
            "partido" : "PSOL",
            "foto" : "http://www3.al.sp.gov.br/repositorio/deputadoPortal/fotos/20150312-160623-id=148-PEQ.jpg",
            "nome" : "Carlos Giannazi",
            "id" : "10592"
        }""")
        actual = ALESPHandler().obter_relatorio(
            "10592",
            "2018-05-18",
            7
        ).to_dict()
        self.maxDiff = None
        self.assertDictEqual(actual["parlamentar"], parlamentar)
        self.assertEqual(len(actual["orgaos"]), 4)
        self.assertEqual(len(actual["proposicoes"]), 7)
        self.assertEqual(len(actual["eventosPresentes"]), 2)
        self.assertEqual(len(actual["eventosPrevistos"]), 0)
        self.assertEqual(len(actual["eventosAusentes"]), 16)
        self.assertEqual(actual["dataFinal"], "18/05/2018")
        self.assertEqual(actual["presencaTotal"], "12.50%")
        self.assertEqual(actual["presencaRelativa"], "100.00%")
        self.assertEqual(actual["dataInicial"], "11/05/2018")
