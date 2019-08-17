import unittest

from legislei.controllers.dto import CustomPresence, MongoDateTime, MongoId

class TestDTOs(unittest.TestCase):

    def test_mongo_datetime_format(self):
        self.assertEqual(MongoDateTime().format("2019-08-10 07:17:00"), "2019-08-10T04:17:00-03:00")
        self.assertEqual(MongoDateTime().format({"$date": 1552521600000}), "2019-03-13T21:00:00-03:00")
        
    def test_mongo_id_format(self):
        self.assertEqual(MongoId().format("5c264b5e3a5efd576ecaf48e"), "5c264b5e3a5efd576ecaf48e")
        self.assertEqual(MongoId().format({"$oid": "5c264b5e3a5efd576ecaf48e"}), "5c264b5e3a5efd576ecaf48e")

    def test_custom_presence(self):
        self.assertEqual(CustomPresence().format(0), "Presente")
        self.assertEqual(CustomPresence().format(1), "Ausência esperada")
        self.assertEqual(CustomPresence().format(2), "Ausente em evento esperado")
        self.assertEqual(CustomPresence().format(3), "Ausente em evento programado")
        self.assertEqual(CustomPresence().format(9), None)
