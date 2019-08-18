import json

from .utils import *

from legislei import controllers

class TestHouseController(ControllerHelperTester):
    
    def test_casas_estados(self):
        actual = self.app.get("/v1/casas/estados")
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertIn("SP", actual_data["casas"])
    
    def test_casas_municipios(self):
        actual = self.app.get("/v1/casas/municipios")
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertIn("SÃO PAULO", actual_data["casas"])
