import unittest
import warnings

from mongoengine import connect

from legislei.exceptions import ItemNotFound, ReportNotFound
from legislei.models.avaliacoes import Avaliacoes
from legislei.models.relatorio import Evento, Parlamentar, Relatorio
from legislei.services.avaliacoes import Avaliacao


class TestAvaliacao(unittest.TestCase):

    def setUp(self):
        connect('mongoenginetest', host='mongomock://localhost')

    def tearDown(self):
        Avaliacoes.drop_collection()

    def test_avaliar_sucesso(self):
        parlamentar = Parlamentar(id='id', cargo='BR1')
        evento = Evento(id='123', nome='Evento')
        relatorio = Relatorio(
            parlamentar=parlamentar,
            data_inicial='2019-01-01',
            eventos_presentes=[evento]
        )
        relatorio.save()

        Avaliacao().avaliar('123', '1', 'test@email.com', relatorio.pk)
        actual = Avaliacoes.objects().first()

        self.assertEqual(actual.email, 'test@email.com')
        self.assertEqual(actual.relatorioId, relatorio.pk)
        self.assertEqual(actual.parlamentar.id, 'id')
        self.assertEqual(actual.parlamentar.cargo, 'BR1')
        self.assertEqual(actual.avaliado['id'], '123')

    def test_avaliar_report_not_found(self):
        with self.assertRaises(ReportNotFound):
            Avaliacao().avaliar('123', '1', 'test@email.com', "4c264b5e3a5efd576ecaf48e")

    def test_avaliar_item_not_found(self):
        parlamentar = Parlamentar(id='id', cargo='BR1')
        relatorio = Relatorio(
            parlamentar=parlamentar,
            data_inicial='2019-01-01'
        )
        relatorio.save()
        
        with self.assertRaises(ItemNotFound):
            Avaliacao().avaliar('123', '1', 'test@email.com', relatorio.pk)

    def test_avaliar_invalid_report_id(self):
        with self.assertRaises(ReportNotFound):
            Avaliacao().avaliar('123', '1', 'test@email.com', "invalid_id")

    def test_deletar_avaliacao_sucesso(self):
        warnings.simplefilter("ignore")
        parlamentar = Parlamentar(id='id', cargo='BR1')
        avaliacao = Avaliacoes(parlamentar=parlamentar, email='test@email.com')
        avaliacao.save()
        avaliacao_id = str(avaliacao.pk)

        Avaliacao().deletar_avaliacao(avaliacao_id)
        actual = Avaliacoes.objects()

        self.assertEqual(len(actual), 0)

    def test_deletar_avaliacao_inexistente(self):
        with self.assertRaises(ItemNotFound):
            Avaliacao().deletar_avaliacao("5c54ecb08f2fa300049d1809")

    def test_deletar_avaliacao_id_invalido(self):
        with self.assertRaises(ItemNotFound):
            Avaliacao().deletar_avaliacao("id_invalido")
    
    def test_minhas_avaliacoes(self):
        parlamentar = Parlamentar(id='id', cargo='BR1')
        avaliacao = Avaliacoes(parlamentar=parlamentar, email='test@email.com')
        avaliacao.save()

        actual = Avaliacao().minhas_avaliacoes('BR1', 'id', 'test@email.com')

        self.assertEqual(actual.first(), avaliacao)

    def test_avaliacoes_de_parlamentar(self):
        parlamentar = Parlamentar(id='id', cargo='BR1')
        avaliacao1 = Avaliacoes(
            parlamentar=parlamentar,
            email='test@email.com',
            relatorioId='4c264b5e3a5efd576ecaf48e',
            avaliacao='-1',
            avaliado={'id': '1'}
        ).save()
        avaliacao2 = Avaliacoes(
            parlamentar=parlamentar,
            email='test@email.com',
            relatorioId='4c264b5e3a5efd576ecaf48e',
            avaliacao='2',
            avaliado={'id': '2'}
        ).save()

        actual = Avaliacao().avaliacoes('BR1', 'id', 'test@email.com')

        self.assertEqual(actual[0], parlamentar)
        self.assertEqual(actual[1], {
            '2': [avaliacao2.to_mongo().to_dict()],
            '1': [],
            '-1': [avaliacao1.to_mongo().to_dict()],
            '-2': []
        })
        self.assertEqual(actual[2], 9)

    def test_avaliacoes_de_parlamentar_sem_avaliacoes(self):
        parlamentar = Parlamentar(id='id', cargo='BR1')

        actual = Avaliacao().avaliacoes('BR1', 'id', 'test@email.com')

        self.assertIsNone(actual[0])
        self.assertIsNone(actual[1])
        self.assertIsNone(actual[2])
