import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from legislei.models.parlamentares import ParlamentaresApp


class TestParlamentaresApp(unittest.TestCase):

    
    def test_obterDataInicial(self):
        par = ParlamentaresApp()
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
        par = ParlamentaresApp()
        actual_response = par.formatarDatasYMD(data_inicial, data_final)
        self.assertEqual(('2018-10-07', '2018-10-28'), actual_response)
