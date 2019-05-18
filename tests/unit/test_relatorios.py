import unittest
from mongoengine import connect
from unittest.mock import patch

from legislei.relatorios import Relatorios
from legislei.models.relatorio import Relatorio, Parlamentar


class TestRelatorios(unittest.TestCase):

    def setUp(self):
        connect('mongoenginetest', host='mongomock://localhost')

    def tearDown(self):
        Relatorio.drop_collection()

    def test_obter_por_id(self):
        parlamentar = Parlamentar(id='id')
        relatorio = Relatorio(parlamentar=parlamentar, data_inicial='2019-01-01')
        relatorio.save()
        
        actual = Relatorios().obter_por_id(relatorio.pk)

        self.assertEqual(relatorio, actual.first())

    def test_buscar_por_parlamentar(self):
        parlamentar_1 = Parlamentar(id='1', cargo='BR1')
        parlamentar_2 = Parlamentar(id='2', cargo='BR1')
        parlamentar_3 = Parlamentar(id='1', cargo='BR2')
        relatorio_1 = Relatorio(parlamentar=parlamentar_1, data_inicial='2019-01-01').save()
        relatorio_2 = Relatorio(parlamentar=parlamentar_2, data_inicial='2019-01-01').save()
        relatorio_3 = Relatorio(parlamentar=parlamentar_3, data_inicial='2019-01-01').save()
        relatorio_4 = Relatorio(parlamentar=parlamentar_1, data_inicial='2019-01-01').save()
        relatorio_5 = Relatorio(parlamentar=parlamentar_3, data_inicial='2019-01-01').save()
        relatorio_6 = Relatorio(parlamentar=parlamentar_2, data_inicial='2019-01-01').save()

        actual = Relatorios().buscar_por_parlamentar('BR1', '1')
        expected = [relatorio_1.to_dict(), relatorio_4.to_dict()]

        self.assertEqual(len(actual), len(expected))

    def test_obter_relatorio_json_existente(self):
        parlamentar = Parlamentar(id='1', cargo='BR1')
        relatorio = Relatorio(parlamentar=parlamentar, data_final='01/01/2019').save()

        actual_response = Relatorios().obter_relatorio('1', '2019-01-01', 'BR1', periodo=7)

        self.assertEqual(actual_response, relatorio.to_dict())

    @patch("legislei.house_selector.house_selector")
    def test_obter_relatorio_json_inexistente_funcao_sem_erro(
        self,
        mock_model_selector
    ):
        parlamentar = Parlamentar(id='1', cargo='BR1')
        relatorio = Relatorio(parlamentar=parlamentar, data_final='01/01/2019')
        class FakeModel:
            def obter_relatorio(self, *args, **kwargs):
                return relatorio
        mock_model_selector.return_value = FakeModel

        actual_response = Relatorios().obter_relatorio('1', '2019-01-01', 'BR1', periodo=7)
        actual_response['_id'] = 'id'
        relatorio.pk = 'id'

        self.assertEqual(actual_response, relatorio.to_dict())
