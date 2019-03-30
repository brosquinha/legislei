import unittest
import warnings
from unittest.mock import patch

from legislei.houses.camara_municipal_sao_paulo import CamaraMunicipalSaoPauloHandler

class TestCamaraMunicipalSaoPauloHandlerIntegration(unittest.TestCase):
    
    def setUp(self):
        warnings.simplefilter("ignore")

    @patch("builtins.print")
    def test_obter_relatorio(self, mock_print):
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
        self.assertEqual(len(actual["orgaos"]), 1)
        self.assertEqual(actual["dataFinal"], "23/03/2019")
        self.assertEqual(actual["dataInicial"], "16/03/2019")
