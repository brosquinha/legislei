import unittest

from legislei.controllers.dto import CustomPresence, MongoDateTime, MongoId, MongoRaw

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

    def test_mongo_raw(self):
        value = {
            "tipo": "PL",
            "urlDocumento": "http://documentacao.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=proje&form=A&nextAction=search&indexSearch=^nTw^lTodos%20os%20campos&exprSearch=P=PL1562019",
            "id": "350290",
            "pauta": None,
            "dataApresentacao": {
                "$date": 1552521600000
            },
            "numero": "1562019",
            "ementa": " DENOMINA PRAÇA MARIELLE FRANCO A PRAÇA INOMINADA COMPREENDIDA ENTRE A EXTENSÃO DA RUA PADRE ACHILLES SILVESTRE E LOGRADOURO INOMINADO.",
            "urlAutores": "http://documentacao.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=proje&form=A&nextAction=search&indexSearch=^nTw^lTodos%20os%20campos&exprSearch=P=PL1562019",
            "voto": None,
            "pautas": [
                {
                    "id": None,
                    "numero": None,
                    "pauta": " ALTERA O ARTIGO 1º DA LEI 16.497/2016 QUE INSTITUI A REDE DE REABILITAÇÃO E CUIDADOS PARA A PESSOA COM DEFICIÊNCIA NO MUNICÍPIO DE SÃO PAULO.",
                    "voto": None,
                    "tipo": "PL 548/2017, do  Ver. ARSELINO TATTO (PT), Ver. TO...",
                    "urlAutores": None,
                    "dataApresentacao": {
                        "$date": 1553690929946
                    },
                    "ementa": None,
                    "urlDocumento": None
                }
            ]
        }
        self.assertEqual(MongoRaw().format(value), {
            "tipo": "PL",
            "urlDocumento": "http://documentacao.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=proje&form=A&nextAction=search&indexSearch=^nTw^lTodos%20os%20campos&exprSearch=P=PL1562019",
            "id": "350290",
            "pauta": None,
            "dataApresentacao": "2019-03-13T21:00:00-03:00",
            "numero": "1562019",
            "ementa": " DENOMINA PRAÇA MARIELLE FRANCO A PRAÇA INOMINADA COMPREENDIDA ENTRE A EXTENSÃO DA RUA PADRE ACHILLES SILVESTRE E LOGRADOURO INOMINADO.",
            "urlAutores": "http://documentacao.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=proje&form=A&nextAction=search&indexSearch=^nTw^lTodos%20os%20campos&exprSearch=P=PL1562019",
            "voto": None,
            "pautas": [
                {
                    "id": None,
                    "numero": None,
                    "pauta": " ALTERA O ARTIGO 1º DA LEI 16.497/2016 QUE INSTITUI A REDE DE REABILITAÇÃO E CUIDADOS PARA A PESSOA COM DEFICIÊNCIA NO MUNICÍPIO DE SÃO PAULO.",
                    "voto": None,
                    "tipo": "PL 548/2017, do  Ver. ARSELINO TATTO (PT), Ver. TO...",
                    "urlAutores": None,
                    "dataApresentacao": "2019-03-27T09:48:49.946000-03:00",
                    "ementa": None,
                    "urlDocumento": None
                }
            ]
        })
