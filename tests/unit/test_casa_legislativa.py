import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from legislei.houses.casa_legislativa import CasaLegislativa


class TestCasaLegislativa(unittest.TestCase):

    
    def test_obterDataInicial(self):
        par = CasaLegislativa()
        self.assertEqual(
            datetime(2018, 10, 21),
            par.obterDataInicial(datetime(2018, 10, 28), weeks=1)
        )
        self.assertEqual(
            datetime(2018, 10, 23),
            par.obterDataInicial(datetime(2018, 10, 28), days=5)
        )

    
    def test_formatarDatasYMD(self):
        data_final = datetime(2018, 10, 28)
        data_inicial = datetime(2018, 10, 7)
        par = CasaLegislativa()
        actual_response = par.formatarDatasYMD(data_inicial, data_final)
        self.assertEqual(('2018-10-07', '2018-10-28'), actual_response)
