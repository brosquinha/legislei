import unittest
from datetime import datetime
from unittest.mock import patch

from legislei.houses.camara_municipal_sao_paulo import CamaraMunicipalSaoPauloHandler

class TestCamaraMunicipalSaoPauloHandler(unittest.TestCase):

    def setUp(self):
        self.cmsp = CamaraMunicipalSaoPauloHandler()

    @patch("builtins.print")
    @patch("legislei.SDKs.CamaraMunicipalSaoPaulo.base.CamaraMunicipal.obterProjetosDetalhes")
    @patch("legislei.SDKs.CamaraMunicipalSaoPaulo.base.CamaraMunicipal.obterProjetosParlamentar")
    def test_obter_proposicoes_parlamentar(
            self,
            mock_obterProjetosParlamentar,
            mock_obterProjetosDetalhes,
            mock_print
    ):
        mock_obterProjetosParlamentar.return_value = [
            {'tipo': 'PL', 'numero': '1', 'ano': '2019'},
            {'tipo': 'PL', 'numero': '3', 'ano': '2019'},
        ]
        mock_obterProjetosDetalhes.return_value = [
            {
                'chave': '1',
                'tipo': 'PL',
                'numero': '1',
                'ano': '2019',
                'ementa': 'Projeto #1',
                'data': '2019-03-26T00:00:00'
            },
            {
                'chave': '2',
                'tipo': 'PL',
                'numero': '2',
                'ano': '2019',
                'ementa': 'Projeto #2',
                'data': '2019-03-26T00:00:00'
            },
            {
                'chave': '3',
                'tipo': 'PL',
                'numero': '3',
                'ano': '2019',
                'ementa': 'Projeto #3',
                'data': '2019-03-26T00:00:00'
            },
        ]

        self.cmsp.obter_proposicoes_parlamentar('123', datetime(2019, 3, 19), datetime(2019, 3, 27))

        self.assertEqual(len(self.cmsp.relatorio.get_proposicoes()), 2)

    @patch("legislei.SDKs.CamaraMunicipalSaoPaulo.base.CamaraMunicipal.obterVereadores")
    def test_obter_parlamentar(self, mock_obterVereadores):
        mock_obterVereadores.return_value = [
            {'chave': '1'},
            {
                'chave': '2',
                'nome': 'Fulana',
                'cargos': [],
                'mandatos': [
                    {'fim': datetime(2020, 12, 31), 'partido': {'sigla': 'TESTE'}},
                    {'fim': datetime(2018, 12, 31)},
                ]
            },
            {'chave': '3'},
        ]

        self.cmsp.obter_parlamentar('2')

        self.assertEqual(self.cmsp.relatorio.get_parlamentar().get_nome(), "Fulana")
        self.assertEqual(self.cmsp.relatorio.get_parlamentar().get_partido(), "TESTE")
        self.assertEqual(self.cmsp.relatorio.get_parlamentar().get_cargo(), "São Paulo".upper())

    def test_obter_cargos_parlamentar(self):
        cargos = [
            {'fim': datetime(2018, 12, 31)},
            {
                'fim': datetime(2020, 12, 31),
                'nome': 'Membro',
                'ente': {'nome': 'Comissão - TESTE'}
            },
            {
                'fim': datetime(2020, 12, 31),
                'nome': 'Presidente',
                'ente': {'nome': 'MESA TESTE'}
            },
            {'fim': datetime(2016, 12, 31)}
        ]

        self.cmsp.obter_cargos_parlamentar(cargos)

        self.assertEqual(len(self.cmsp.relatorio.get_orgaos()), 2)
    
    @patch("legislei.SDKs.CamaraMunicipalSaoPaulo.base.CamaraMunicipal.obterVereadores")
    def test_obter_parlamentares(self, mock_obterVereadores):
        mock_obterVereadores.return_value = [
            {
                'chave': '1',
                'nome': 'Fulano',
                'mandatos': [
                    {'fim': datetime(2020, 12, 31), 'partido': {'sigla': 'TESTE'}}
                ]
            },
            {
                'chave': '2',
                'nome': 'Fulana',
                'mandatos': [
                    {'fim': datetime(2020, 12, 31), 'partido': {'sigla': 'TESTE'}},
                    {'fim': datetime(2018, 12, 31)},
                ]
            },
            {
                'chave': '3',
                'nome': 'Joana',
                'mandatos': [
                    {'fim': datetime(2020, 12, 31), 'partido': {'sigla': 'TESTE'}},
                    {'fim': datetime(2018, 12, 31)},
                ]
            },
        ]

        actual = self.cmsp.obter_parlamentares()

        self.assertEqual(actual, [
            {'nome': 'Fulano', 'id': '1', 'siglaPartido': 'TESTE'},
            {'nome': 'Fulana', 'id': '2', 'siglaPartido': 'TESTE'},
            {'nome': 'Joana', 'id': '3', 'siglaPartido': 'TESTE'}
        ])

