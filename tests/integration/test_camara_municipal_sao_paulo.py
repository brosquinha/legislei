import logging
import unittest
import warnings
from datetime import datetime
from unittest.mock import patch

import pytz

from legislei.houses.camara_municipal_sao_paulo import CamaraMunicipalSaoPauloHandler

class TestCamaraMunicipalSaoPauloHandlerIntegration(unittest.TestCase):
    
    def setUp(self):
        warnings.simplefilter("ignore")
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_obter_relatorio(self):
        brasilia_tz = pytz.timezone('America/Sao_Paulo')

        actual = CamaraMunicipalSaoPauloHandler().obter_relatorio(
            "2185",
            "2019-03-23",
            7
        ).to_dict()

        self.assertEqual(actual["parlamentar"]["nome"], "CELSO GIANNAZI")
        self.assertEqual(len(actual["eventosAusentes"]), 0)
        self.assertEqual(len(actual["eventosPrevistos"]), 0)
        self.assertEqual(len(actual["eventosPresentes"]), 7)
        self.assertEqual(len(actual["proposicoes"]), 2)
        self.assertEqual(actual["dataFinal"], brasilia_tz.localize(datetime(2019, 3, 23)))
        self.assertEqual(actual["dataInicial"], brasilia_tz.localize(datetime(2019, 3, 16)))
