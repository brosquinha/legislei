import json
import logging
import unittest
import warnings
from datetime import datetime
from unittest.mock import patch

import pytz

from legislei.houses.alesp import ALESPHandler


class TestALESPHandlerIntegration(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter("ignore")
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)
    
    def test_obter_relatorio(self):
        brasilia_tz = pytz.timezone('America/Sao_Paulo')
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
        self.assertEqual(actual["dataFinal"], brasilia_tz.localize(datetime(2018, 5, 18)))
        self.assertEqual(actual["presencaTotal"], "11.11%")
        self.assertEqual(actual["presencaRelativa"], "100.00%")
        self.assertEqual(actual["dataInicial"], brasilia_tz.localize(datetime(2018, 5, 11)))
