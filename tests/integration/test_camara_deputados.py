import json
import logging
import unittest
import warnings
from datetime import date, datetime
from unittest.mock import patch

import pytz

from legislei.houses.camara_deputados import CamaraDeputadosHandler


class TestCamaraDeputadosHandlerIntegration(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter("ignore")
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)
    
    def test_obter_relatorio(self):
        brasilia_tz = pytz.timezone('America/Sao_Paulo')
        parlamentar = json.loads("""{
            "cargo" : "BR1",
            "uf" : "RJ",
            "partido" : "PSOL",
            "foto" : "https://www.camara.leg.br/internet/deputado/bandep/74171.jpg",
            "nome" : "CHICO ALENCAR",
            "id" : "74171"
        }""")
        
        actual = CamaraDeputadosHandler().obter_relatorio(
            "74171",
            "2018-06-29",
            7
        ).to_dict()
        self.maxDiff = None
        self.assertDictEqual(actual["parlamentar"], parlamentar)
        self.assertGreaterEqual(len(actual["eventosAusentes"]), 50)
        self.assertEqual(len(actual["eventosPrevistos"]), 3)
        self.assertEqual(len(actual["eventosPresentes"]), 6)
        self.assertEqual(len(actual["proposicoes"]), 4)
        self.assertEqual(len(actual["orgaos"]), 15)
        self.assertEqual(actual["dataFinal"], brasilia_tz.localize(datetime(2018, 6, 29)))
        self.assertEqual(actual["eventosAusentesEsperadosTotal"], 3)
        self.assertEqual(actual["dataInicial"], brasilia_tz.localize(datetime(2018, 6, 22)))

    def test_obter_parlamentares(self):
        expected = 512
        actual = CamaraDeputadosHandler().obter_parlamentares()
        self.assertGreaterEqual(len(actual), expected)

    def test_obter_parlamentar(self):
        expected = json.loads("""{
            "cargo" : "BR1",
            "uf" : "RJ",
            "partido" : "PSOL",
            "foto" : "https://www.camara.leg.br/internet/deputado/bandep/74171.jpg",
            "nome" : "CHICO ALENCAR",
            "id" : "74171"
        }""")
        actual = CamaraDeputadosHandler().obter_parlamentar("74171").to_dict()
        self.assertDictEqual(actual, expected)
