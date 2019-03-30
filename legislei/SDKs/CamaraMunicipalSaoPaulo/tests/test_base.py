import unittest
import warnings

from legislei.SDKs.CamaraMunicipalSaoPaulo.base import CamaraMunicipal

class TestCamaraMunicipal(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter("ignore")
    
    def test_obterVereadores(self):
        cmsp = CamaraMunicipal()

        actual = cmsp.obterVereadores()

        self.assertGreaterEqual(len(actual), 55)
