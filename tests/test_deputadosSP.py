import unittest
from unittest.mock import patch
from datetime import datetime
from models.deputadosSP import DeputadosALESPApp
from models.relatorio import Parlamentar

class TestDeputadosSPApp(unittest.TestCase):

    def setUp(self):
        self.dep = DeputadosALESPApp()

    @patch("SDKs.AssembleiaLegislativaSP.deputados.Deputados.obterTodosDeputados")
    def test_obterDeputado(self, mock_obterTodosDeputados):
        mock_obterTodosDeputados.return_value = [
            {'id': '12'},
            {'id': '11'},
            {'id': '14', 'nome': 'Teste', 'siglaPartido': 'PPP', 'urlFoto': 'foto'},
        ]
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

    @patch("SDKs.AssembleiaLegislativaSP.deputados.Deputados.obterTodosDeputados")
    def test_obterParlamentares(self, mock_obterTodosDeputados):
        mock_obterTodosDeputados.return_value = [
            {'id': '12'},
            {'id': '11'},
            {'id': '14', 'nome': 'Teste'},
        ]

        actual_response = self.dep.obter_parlamentares()

        self.assertEqual(mock_obterTodosDeputados.return_value, actual_response)

    @patch("SDKs.AssembleiaLegislativaSP.comissoes.Comissoes.obterComissoes")
    def test_obterComissoesPorId(self, mock_obterComissoes):
        mock_obterComissoes.return_value = [
            {'id': '1', 'nome': 'Comissão1'},
            {'id': '2', 'nome': 'Comissão2'},
            {'id': '3', 'nome': 'Comissão3'},
        ]

        actual_response = self.dep.obterComissoesPorId()

        self.assertEqual({
            '1': {'id': '1', 'nome': 'Comissão1'},
            '2': {'id': '2', 'nome': 'Comissão2'},
            '3': {'id': '3', 'nome': 'Comissão3'}
            }, actual_response)

    @patch("SDKs.AssembleiaLegislativaSP.comissoes.Comissoes.obterVotacoesComissoes")
    def test_obterVotacoesPorReuniao(self, mock_obterVotacoesComissoes):
        mock_obterVotacoesComissoes.return_value = [
            {'idDeputado': '1', 'idReuniao': '1', 'voto': 'F'},
            {'idDeputado': '1', 'idReuniao': '2', 'voto': 'F'},
            {'idDeputado': '2', 'idReuniao': '3', 'voto': 'S'},
            {'idDeputado': '3', 'idReuniao': '4', 'voto': 'F'},
            {'idDeputado': '1', 'idReuniao': '1', 'voto': 'C'},
            {'idDeputado': '4', 'idReuniao': '5', 'voto': 'C'},
        ]

        actual_response = self.dep.obterVotacoesPorReuniao('1')

        self.assertEqual({
            '1': [
                {'idDeputado': '1', 'idReuniao': '1', 'voto': 'F'},
                {'idDeputado': '1', 'idReuniao': '1', 'voto': 'C'},
            ],
            '2': [{'idDeputado': '1', 'idReuniao': '2', 'voto': 'F'}]
        }, actual_response)

    @patch("models.deputadosSP.DeputadosALESPApp.obterDatetimeDeStr")
    @patch("SDKs.AssembleiaLegislativaSP.comissoes.Comissoes.obterMembrosComissoes")
    def test_obterComissoesDeputado(
        self,
        mock_obterMembrosComissoes,
        mock_obterDatetimeDeStr
    ):
        def fakeObterDatetimeDeStr(txt):
            return txt
        mock_obterDatetimeDeStr.side_effect = fakeObterDatetimeDeStr
        mock_obterMembrosComissoes.return_value = [
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
            len(self.dep.relatorio.get_orgaos()), 3
        )
        self.assertTrue(mock_obterDatetimeDeStr.called)

    @patch("models.deputadosSP.DeputadosALESPApp.obterDatetimeDeStr")
    @patch("SDKs.AssembleiaLegislativaSP.comissoes.Comissoes.obterPresencaReunioesComissoes")
    @patch("SDKs.AssembleiaLegislativaSP.comissoes.Comissoes.obterReunioesComissoes")
    def test_obterEventosPresentes(
        self,
        mock_obterReunioesComissoes,
        mock_obterPresencaReunioes,
        mock_obterDatetimeDeStr
    ):
        def fakeObterDatetimeDeStr(txt):
            return txt
        mock_obterDatetimeDeStr.side_effect = fakeObterDatetimeDeStr
        mock_obterReunioesComissoes.return_value = [
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
        mock_obterPresencaReunioes.return_value = [
            {'idDeputado': '1', 'idReuniao': '1'},
            {'idDeputado': '1', 'idReuniao': '2'},
            {'idDeputado': '1', 'idReuniao': '3'},
            {'idDeputado': '2', 'idReuniao': '6'},
        ]
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

        self.assertEqual(len(self.dep.relatorio.get_eventos_presentes()), 1)
        self.assertEqual(len(self.dep.relatorio.get_eventos_ausentes()), 4)
        self.assertEqual(len(self.dep.relatorio.get_eventos_previstos()), 1)

    @patch("builtins.print")
    @patch("models.deputadosSP.DeputadosALESPApp.obterDatetimeDeStr")
    @patch("SDKs.AssembleiaLegislativaSP.proposicoes.Proposicoes.obterTodasProposicoes")
    @patch("SDKs.AssembleiaLegislativaSP.proposicoes.Proposicoes.obterTodosAutoresProposicoes")
    @patch("SDKs.AssembleiaLegislativaSP.proposicoes.Proposicoes.obterNaturezaDocumentos")
    def test_obterProposicoesDeputado(
        self,
        mock_obterNaturezaDocumentos,
        mock_obterTodosAutoresProposicoes,
        mock_obterTodasProposicoes,
        mock_obterDatetimeDeStr,
        mock_print
    ):
        def fakeObterDatetimeDeStr(txt):
            return txt
        mock_obterDatetimeDeStr.side_effect = fakeObterDatetimeDeStr
        mock_obterNaturezaDocumentos.return_value = [
            {'id': '1', 'sigla': 'PL'},
            {'id': '2', 'sigla': 'PEC'},
            {'id': '3', 'sigla': 'REQ'},
        ]
        mock_obterTodosAutoresProposicoes.return_value = [
            {'idAutor': '1', 'idDocumento': '1'},
            {'idAutor': '2', 'idDocumento': '2'},
            {'idAutor': '1', 'idDocumento': '3'},
            {'idAutor': '1', 'idDocumento': '4'},
            {'idAutor': '1', 'idDocumento': '5'},
        ]
        mock_obterTodasProposicoes.return_value = [
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

        self.dep.obterProposicoesDeputado(
            '1', datetime(2018, 12, 10), datetime(2018, 12, 16)
        )

        self.assertEqual(len(self.dep.relatorio.get_proposicoes()), 2)

    def test_obterDatetimeDeStr(self):
        actual_response = self.dep.obterDatetimeDeStr('2018-12-15T00:00:00')
        self.assertEqual(datetime(2018, 12, 15), actual_response)
