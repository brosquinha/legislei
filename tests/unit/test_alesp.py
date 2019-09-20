import logging
import unittest
from datetime import datetime
from unittest.mock import patch

from legislei.exceptions import ModelError
from legislei.houses.alesp import ALESPHandler
from legislei.models.relatorio import Parlamentar
from legislei.SDKs.AssembleiaLegislativaSP.exceptions import ALESPError
from legislei.SDKs.AssembleiaLegislativaSP.mock import Mocker


class TestALESPHandler(unittest.TestCase):

    def setUp(self):
        self.dep = ALESPHandler()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_obterDeputado(self):
        mock = Mocker(self.dep.dep)
        mock.add_response(
            "obterTodosDeputados",
            [
                {'id': '12'},
                {'id': '11'},
                {'id': '14', 'nome': 'Teste', 'siglaPartido': 'PPP', 'urlFoto': 'foto'},
            ]
        )
        expected_response = {
            'id': '14',
            'nome': 'Teste',
            'partido': 'PPP',
            'uf': 'SP',
            'cargo': 'SP',
            'foto': 'foto'
        }

        actual_response = self.dep.obter_parlamentar('14')

        self.assertEqual(expected_response, actual_response.to_dict())
        mock.assert_no_pending_responses()

    def test_obterParlamentares(self):
        mock = Mocker(self.dep.dep)
        mock_response = [
            {'id': '12', 'nome': 'Teste2', 'siglaPartido': 'P1'},
            {'id': '11', 'nome': 'Teste1', 'siglaPartido': 'P2'},
            {'id': '14', 'nome': 'Teste4', 'siglaPartido': 'P1'},
        ]
        expected_response = [
            Parlamentar(
                id='12',
                nome='Teste2',
                partido='P1',
                cargo='SP',
                uf='SP',
                foto=None
            ),
            Parlamentar(
                id='11',
                nome='Teste1',
                partido='P2',
                cargo='SP',
                uf='SP',
                foto=None
            ),
            Parlamentar(
                id='14',
                nome='Teste4',
                partido='P1',
                cargo='SP',
                uf='SP',
                foto=None
            )
        ]
        mock.add_response("obterTodosDeputados", mock_response)

        actual_response = self.dep.obter_parlamentares()

        self.assertEqual(expected_response, actual_response)
        mock.assert_no_pending_responses()

    def test_obterParlamentares_fail_case(self):
        mock = Mocker(self.dep.dep)
        mock.add_exception("obterTodosDeputados", ALESPError)

        with self.assertRaises(ModelError):
            self.dep.obter_parlamentares()

        mock.assert_no_pending_responses()

    def test_obterComissoesPorId(self):
        mock = Mocker(self.dep.com)
        mock.add_response(
            "obterComissoes",
            [
                {'id': '1', 'nome': 'Comissão1'},
                {'id': '2', 'nome': 'Comissão2'},
                {'id': '3', 'nome': 'Comissão3'},
            ]
        )

        actual_response = self.dep.obterComissoesPorId()

        self.assertEqual({
            '1': {'id': '1', 'nome': 'Comissão1'},
            '2': {'id': '2', 'nome': 'Comissão2'},
            '3': {'id': '3', 'nome': 'Comissão3'}
            }, actual_response)
        mock.assert_no_pending_responses()

    def test_obterVotacoesPorReuniao(self):
        mock = Mocker(self.dep.com)
        mock.add_response(
            "obterVotacoesComissoes",
            [
                {'idDeputado': '1', 'idReuniao': '1', 'voto': 'F'},
                {'idDeputado': '1', 'idReuniao': '2', 'voto': 'F'},
                {'idDeputado': '2', 'idReuniao': '3', 'voto': 'S'},
                {'idDeputado': '3', 'idReuniao': '4', 'voto': 'F'},
                {'idDeputado': '1', 'idReuniao': '1', 'voto': 'C'},
                {'idDeputado': '4', 'idReuniao': '5', 'voto': 'C'},
            ]
        )

        actual_response = self.dep.obterVotacoesPorReuniao('1')

        self.assertEqual({
            '1': [
                {'idDeputado': '1', 'idReuniao': '1', 'voto': 'F'},
                {'idDeputado': '1', 'idReuniao': '1', 'voto': 'C'},
            ],
            '2': [{'idDeputado': '1', 'idReuniao': '2', 'voto': 'F'}]
        }, actual_response)
        mock.assert_no_pending_responses()

    def test_obterVotoDescritivo(self):
        self.assertEqual(self.dep.obterVotoDescritivo("F"), "Favorável")
        self.assertEqual(self.dep.obterVotoDescritivo("C"), "Contrário")
        self.assertEqual(self.dep.obterVotoDescritivo("S"), "Com o voto em separado")
        self.assertEqual(self.dep.obterVotoDescritivo("WTF"), "WTF")

    @patch("legislei.houses.alesp.ALESPHandler.obterDatetimeDeStr")
    def test_obterComissoesDeputado(
        self,
        mock_obterDatetimeDeStr
    ):
        def fakeObterDatetimeDeStr(txt):
            return txt
        mock_obterDatetimeDeStr.side_effect = fakeObterDatetimeDeStr
        mock = Mocker(self.dep.com)
        mock.add_response(
            "obterMembrosComissoes",
            [
                {
                    'idDeputado': '1',
                    'idComissao': '1',
                    'dataInicio': datetime(2018, 12, 1),
                    'dataFim': datetime(2018, 12, 30),
                    'efetivo': True
                },
                {
                    'idDeputado': '1',
                    'idComissao': '2',
                    'dataInicio': datetime(2018, 12, 1),
                    'dataFim': None,
                    'efetivo': True
                },
                {
                    'idDeputado': '1',
                    'idComissao': '3',
                    'dataInicio': datetime(2018, 12, 1),
                    'dataFim': datetime(2018, 12, 30),
                    'efetivo': False
                },
                {
                    'idDeputado': '2',
                    'idComissao': '4',
                    'dataFim': datetime(2018, 11, 30),
                    'dataInicio': datetime(2018, 11, 1),
                    'efetivo': True
                }
            ]
        )
        comissoes = {
            '1': {'nome': 'Comissão1', 'sigla': 'C1'},
            '2': {'nome': 'Comissão2', 'sigla': 'C2'},
            '3': {'nome': 'Comissão3', 'sigla': 'C3'},
            '4': {'nome': 'Comissão3', 'sigla': 'C4'},
        }

        actual_response = self.dep.obterComissoesDeputado(
            comissoes, '1', datetime(2018, 12, 10), datetime(2018, 12, 14)
        )
        
        self.assertEqual(['C1', 'C2', 'C3'], actual_response)
        self.assertEqual(
            len(self.dep.relatorio.orgaos), 3
        )
        self.assertTrue(mock_obterDatetimeDeStr.called)
        mock.assert_no_pending_responses()

    @patch("legislei.houses.alesp.ALESPHandler.obterDatetimeDeStr")
    def test_obterEventosPresentes(
        self,
        mock_obterDatetimeDeStr
    ):
        def fakeObterDatetimeDeStr(txt):
            return txt
        mock_obterDatetimeDeStr.side_effect = fakeObterDatetimeDeStr
        mock = Mocker(self.dep.com)
        mock.add_response(
            "obterReunioesComissoes",
            [
                {
                    'id': '1',
                    'idComissao': '1',
                    'convocacao': 'Reunião1',
                    'situacao': 'Realizada',
                    'data': datetime(2018, 12, 15),
                },
                {
                    'id': '2',
                    'idComissao': '1',
                    'convocacao': 'Reunião2',
                    'situacao': 'Realizada',
                    'data': datetime(2018, 12, 1),
                },
                {
                    'id': '3',
                    'idComissao': '1',
                    'convocacao': 'Reunião3',
                    'situacao': 'Em preparação',
                    'data': datetime(2018, 12, 30),
                },
                {
                    'id': '4',
                    'idComissao': '1',
                    'convocacao': 'Reunião4',
                    'situacao': 'Cancelada',
                    'data': datetime(2018, 12, 15),
                },
                {
                    'id': '5',
                    'idComissao': '2',
                    'convocacao': 'Reunião1',
                    'situacao': 'Realizada',
                    'data': datetime(2018, 12, 15),
                },
                {
                    'id': '6',
                    'idComissao': '2',
                    'convocacao': 'Reunião2',
                    'situacao': 'Realizada',
                    'data': datetime(2018, 12, 15),
                },
                {
                    'id': '7',
                    'idComissao': '1',
                    'convocacao': 'Reunião5',
                    'situacao': 'Realizada',
                    'data': datetime(2018, 12, 15),
                },
            ]
        )
        mock.add_response(
            "obterPresencaReunioesComissoes",
            [
                {'idDeputado': '1', 'idReuniao': '1'},
                {'idDeputado': '1', 'idReuniao': '2'},
                {'idDeputado': '1', 'idReuniao': '3'},
                {'idDeputado': '2', 'idReuniao': '6'},
            ]
        )
        reunioes = {
            '1': [{'idDocumento': '1', 'voto': 'F'}],
        }
        comissoes = {
            '1': {'nome': 'Comissão1', 'sigla': 'C1'},
            '2': {'nome': 'Comissão2', 'sigla': 'C2'},
        }

        self.dep.obterEventosPresentes(
            '1',
            datetime(2018, 12, 10),
            datetime(2018, 12, 16),
            reunioes,
            comissoes,
            ['C1']
        )

        self.assertEqual(len(self.dep.relatorio.eventos_presentes), 1)
        self.assertEqual(len(self.dep.relatorio.eventos_ausentes), 4)
        self.assertEqual(len(self.dep.relatorio.eventos_previstos), 1)
        mock.assert_no_pending_responses()

    @patch("legislei.houses.alesp.ALESPHandler.obterDatetimeDeStr")
    @patch("legislei.SDKs.AssembleiaLegislativaSP.proposicoes.Proposicoes.obterTodasProposicoes")
    @patch("legislei.SDKs.AssembleiaLegislativaSP.proposicoes.Proposicoes.obterTodosAutoresProposicoes")
    @patch("legislei.SDKs.AssembleiaLegislativaSP.proposicoes.Proposicoes.obterNaturezaDocumentos")
    def test_obterProposicoesDeputado(
        self,
        mock_obterNaturezaDocumentos,
        mock_obterTodosAutoresProposicoes,
        mock_obterTodasProposicoes,
        mock_obterDatetimeDeStr
    ):
        def fakeObterDatetimeDeStr(txt):
            return txt
        mock_obterDatetimeDeStr.side_effect = fakeObterDatetimeDeStr
        mock = Mocker(self.dep.prop)
        mock.add_response(
            "obterNaturezaDocumentos",
            [
                {'id': '1', 'sigla': 'PL'},
                {'id': '2', 'sigla': 'PEC'},
                {'id': '3', 'sigla': 'REQ'},
            ]
        )
        mock.add_response(
            "obterTodosAutoresProposicoes",
            [
                {'idAutor': '1', 'idDocumento': '1'},
                {'idAutor': '2', 'idDocumento': '2'},
                {'idAutor': '1', 'idDocumento': '3'},
                {'idAutor': '1', 'idDocumento': '4'},
                {'idAutor': '1', 'idDocumento': '5'},
            ]
        )
        mock.add_response(
            "obterTodasProposicoes",
            [
                {
                    'id': '1',
                    'ementa': 'Faz coisas boas',
                    'numero': '001',
                    'dataEntrada': datetime(2018, 12, 15),
                    'idNatureza': '1'
                },
                {
                    'id': '2',
                    'ementa': 'Faz outras coisas boas',
                    'numero': '002',
                    'dataEntrada': datetime(2018, 12, 15),
                    'idNatureza': '1'
                },
                {
                    'id': '3',
                    'ementa': 'Não tenho data de entrada',
                    'numero': '002',
                    'dataEntrada': None,
                    'idNatureza': '1'
                },
                {
                    'id': '4',
                    'ementa': 'Não tenho natureza',
                    'numero': '003',
                    'dataEntrada': datetime(2018, 12, 15),
                    'idNatureza': None
                },
                {
                    'id': '5',
                    'ementa': 'Não faço parte do perído do relatório',
                    'numero': '005',
                    'dataEntrada': datetime(2018, 12, 1),
                    'idNatureza': '1'
                },
            ]
        )

        self.dep.obterProposicoesDeputado(
            '1', datetime(2018, 12, 10), datetime(2018, 12, 16)
        )

        self.assertEqual(len(self.dep.relatorio.proposicoes), 2)
        mock.assert_no_pending_responses()

    def test_obterDatetimeDeStr(self):
        actual_response = self.dep.obterDatetimeDeStr('2018-12-15T00:00:00')
        self.assertEqual(datetime(2018, 12, 15), actual_response)
