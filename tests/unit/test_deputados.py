import json
import unittest
from datetime import datetime
from unittest.mock import patch

from models.deputados import DeputadosApp
from models.relatorio import Evento, Orgao, Parlamentar, Proposicao, Relatorio
from SDKs.CamaraDeputados.entidades import Deputados
from SDKs.CamaraDeputados.mock import Mocker
from SDKs.CamaraDeputados.exceptions import CamaraDeputadosError


class TestDeputadosApp(unittest.TestCase):

    def setUp(self):
        self.dep = DeputadosApp()

    def test_obterParlamentares(self):
        def fakeObterDeputados():
            yield [{'nome': 'CESAR DA SILVA'}, {'nome': 'FULANO PESSOA'}]
            yield [{'nome': 'SICRANO PINTO'}]
        mock = Mocker(self.dep.dep)
        mock.add_response('obterTodosDeputados', fakeObterDeputados())
        actual_response = self.dep.obter_parlamentares()
        self.assertEqual(actual_response, [
            {'nome': 'CESAR DA SILVA'},
            {'nome': 'FULANO PESSOA'},
            {'nome': 'SICRANO PINTO'}
        ])

    @patch("models.parlamentares.ParlamentaresApp.formatarDatasYMD")
    @patch("models.parlamentares.ParlamentaresApp.obterDataInicial")
    def test_obterOrgaosDeputado(
            self,
            mock_obterDataInicial,
            mock_formatarDatasYMD
    ):
        mock = Mocker(self.dep.dep)
        mock.add_response(
            "obterOrgaosDeputado",
            [[
                {'nomeOrgao': 'Comissão A', 'dataFim': None},
                {'nomeOrgao': 'Comissão B', 'dataFim': '2018-08-31'},
                {'nomeOrgao': 'Comissão C', 'dataFim': '2018-12-31'}
            ]],
            '1234',
            dataInicial='2018-10-21'
        )
        mock_obterDataInicial.return_value = datetime(2018, 10, 21)
        mock_formatarDatasYMD.return_value = ('2018-10-21')

        actual_response = self.dep.obterOrgaosDeputado(
            '1234', datetime(2018, 10, 28))

        self.assertIn({'nomeOrgao': 'Comissão A', 'dataFim': None}, actual_response)
        self.assertIn(
            {'nomeOrgao': 'Comissão C', 'dataFim': '2018-12-31'}, actual_response)
        self.assertEqual(len(actual_response), 2)

        mock.assert_no_pending_responses()
        mock_obterDataInicial.assert_called_once_with(
            datetime(2018, 10, 28), days=7)
        mock_formatarDatasYMD.assert_called_once_with(datetime(2018, 10, 21))

    def test_obterOrgaosDeputado_fail_case(self):
        mock = Mocker(self.dep.dep)
        mock.add_exception('obterOrgaosDeputado', CamaraDeputadosError)

        actual_response = self.dep.obterOrgaosDeputado('1234', datetime(2018, 10, 28))

        self.assertEqual(actual_response, [{'nomeOrgao': None}])
        mock.assert_no_pending_responses()

    @patch("models.parlamentares.ParlamentaresApp.obterDataInicialEFinal")
    def test_procurarEventosComDeputado(
            self,
            mock_obterDataInicialEFinal
    ):
        mock = Mocker(self.dep.ev)
        mock.add_response(
            "obterTodosEventos",
            [
                [{'id': '123'}, {'id': '1234'}],
                [{'id': '12345'}]
            ],
            dataInicio='2018-10-21', dataFim='2018-10-28'
        )
        mock.add_response(
            "obterDeputadosEvento",
            [{'id': '12345'}, {'id': '98765'}],
            "123"
        )
        mock.add_response(
            "obterDeputadosEvento",
            [{'id': '98765'}, {'id': '34567'}],
            "1234"
        )
        mock.add_response(
            "obterDeputadosEvento",
            [{'id': '12345'}, {'id': '98765'}],
            "12345"
        )
        mock_obterDataInicialEFinal.return_value = ('2018-10-21', '2018-10-28')
        dep_id = '12345'

        actual_response = self.dep.procurarEventosComDeputado(
            dep_id, data_final=datetime(2018, 10, 28))

        self.assertEqual([
            {'id': '123'}, {'id': '12345'}
        ], actual_response[0])
        self.assertEqual(200/3, actual_response[1])
        self.assertEqual([
            {'id': '123'},
            {'id': '1234'},
            {'id': '12345'}
        ], actual_response[2])

        mock_obterDataInicialEFinal.assert_called_once_with(
            datetime(2018, 10, 28))
        mock.assert_no_pending_responses()

    def test_procurarEventosComDeputado_fail_case(self):
        mock = Mocker(self.dep.dep)
        mock.add_exception("obterEventosDeputado", CamaraDeputadosError)

        actual_response = self.dep.obterEventosPrevistosDeputado("123", datetime(2018, 10, 28))

        self.assertEqual(actual_response, [{'id': None}])
        mock.assert_no_pending_responses()

    @patch("models.parlamentares.ParlamentaresApp.obterDataInicialEFinal")
    def test_obterEventosPrevistosDeputado(
            self,
            mock_obterDataInicialEFinal,
    ):
        eventos = [
            {'nome': 'Evento 1'},
            {'nome': 'Evento 2'},
            {'nome': 'Evento 3'}
        ]
        dep_id = '12345'
        mock = Mocker(self.dep.dep)
        mock.add_response(
            "obterEventosDeputado",
            [eventos],
            dep_id,
            dataInicio='2018-10-21',
            dataFim='2018-10-28'
        )

        mock_obterDataInicialEFinal.return_value = ('2018-10-21', '2018-10-28')

        actual_response = self.dep.obterEventosPrevistosDeputado(
            dep_id, datetime(2018, 10, 28))

        self.assertEqual(eventos, actual_response)

        mock_obterDataInicialEFinal.assert_called_once_with(
            datetime(2018, 10, 28))
        mock.assert_no_pending_responses()

    def test_obterPautaEvento(
            self,
    ):
        ev_id = '1234'
        mock_ev = Mocker(self.dep.ev)
        mock_ev.add_response(
            "obterPautaEvento",
            [
                {
                    'codRegime': '123',
                    'proposicao_': {
                        'id': '12345'
                    }
                },
                {
                    'codRegime': '123',
                    'proposicao_': {
                        'id': '12345'
                    }
                },
                {
                    'codRegime': '987',
                    'proposicao_': {
                        'id': '98765'
                    }
                },
                {
                    'codRegime': '987',
                    'proposicao_': {
                        'id': '56789'
                    }
                },
            ],
            ev_id
        )
        mock_prop = Mocker(self.dep.prop)
        mock_prop.add_response(
            "obterProposicao",
            {'nome': 'Proposição I'},
            "12345"
        )
        mock_prop.add_response(
            "obterProposicao",
            {'nome': 'Proposição II'},
            "98765"
        )
        mock_prop.add_exception("obterProposicao", CamaraDeputadosError, "56789")
        mock_prop.add_response(
            "obterVotacoesProposicao",
            {'votos': '512'},
            "12345"
        )
        mock_prop.add_response(
            "obterVotacoesProposicao",
            {'votos': '256'},
            "98765"
        )
        mock_prop.add_exception("obterVotacoesProposicao", CamaraDeputadosError, "56789")

        actual_response = self.dep.obterPautaEvento(ev_id)

        self.assertEqual(actual_response, [
            {
                'codRegime': '123',
                'proposicao_': {
                    'id': '12345'
                },
                'proposicao_detalhes': {'nome': 'Proposição I'},
                'votacao': {'votos': '512'}
            },
            {
                'codRegime': '987',
                'proposicao_': {
                    'id': '98765'
                },
                'proposicao_detalhes': {'nome': 'Proposição II'},
                'votacao': {'votos': '256'}
            },
            {
                'codRegime': '987',
                'proposicao_': {
                    'id': '56789'
                },
                'proposicao_detalhes': [{'error': True}],
                'votacao': [{'error': True}]
            },
        ])

        mock_ev.assert_no_pending_responses()
        mock_prop.assert_no_pending_responses()

    def test_obterPautaEvento_error_case(self):
        mock = Mocker(self.dep.ev)
        mock.add_exception("obterPautaEvento", CamaraDeputadosError, "12345")

        actual_response = self.dep.obterPautaEvento("12345")

        self.assertEqual(actual_response, [{'error': True}])
        mock.assert_no_pending_responses()

    def test_obterVotoDeputado(
            self,
    ):
        votos = [
            {
                'parlamentar': {'id': '12345'},
                'voto': 'Sim'
            },
            {
                'parlamentar': {'id': '23456'},
                'voto': 'Não'
            },
            {
                'parlamentar': {'id': '34567'},
                'voto': 'Abstenção'
            }
        ]
        mock = Mocker(self.dep.vot)
        mock.add_response(
            "obterVotos",
            [votos]
        )

        actual_response = self.dep.obterVotoDeputado('', '12345')

        self.assertEqual('Sim', actual_response)
        mock.assert_no_pending_responses()

    def test_obterVotoDeputado_fail_case(self):
        mock = Mocker(self.dep.vot)
        mock.add_exception("obterVotos", CamaraDeputadosError, "12345")

        actual_response = self.dep.obterVotoDeputado("12345", "67890")

        self.assertEqual(actual_response, False)
        mock.assert_no_pending_responses()

    @patch("models.deputados.DeputadosApp.obterEventosPrevistosDeputado")
    def test_obterEventosAusentes(
        self,
        mock_obterEventosPrevistosDeputado
    ):
        mock_obterEventosPrevistosDeputado.return_value = [
            {'id': '2'},
            {'id': '3'},
            {'id': '4'},
        ]
        todos_eventos = [
            {'id': '1', 'orgaos': [{'nome': 'Órgão 1', 'apelido': ''}]},
            {'id': '2', 'orgaos': [{'nome': 'Órgão 1', 'apelido': ''}]},
            {'id': '3', 'orgaos': [{'nome': 'Órgão 2', 'apelido': ''}]},
            {'id': '4', 'orgaos': [{'nome': 'Órgão 2', 'apelido': ''}]},
            {'id': '5', 'orgaos': [{'nome': 'Órgão 4', 'apelido': ''}]},
            {'id': '6', 'orgaos': [{'nome': 'Órgão 4', 'apelido': 'PLEN'}]},
        ]
        dep_eventos = [
            {'orgaos': [{'nome': 'Órgão 2', 'apelido': ''}], 'id': '3'},
            {'id': '4', 'orgaos': [{'nome': 'Órgão 2', 'apelido': ''}]},
        ]

        actual_response = self.dep.obterEventosAusentes(
            '123',
            datetime(2018, 10, 28),
            dep_eventos,
            ['Órgão 1', 'Órgão 2', 'Órgão 3'],
            todos_eventos
        )

        self.assertEqual([
            {'id': '1', 'orgaos': [
                {'nome': 'Órgão 1', 'apelido': ''}], 'controleAusencia': 2},
            {'id': '2', 'orgaos': [
                {'nome': 'Órgão 1', 'apelido': ''}], 'controleAusencia': 1},
            {'id': '5', 'orgaos': [
                {'nome': 'Órgão 4', 'apelido': ''}], 'controleAusencia': None},
            {'id': '6', 'orgaos': [
                {'nome': 'Órgão 4', 'apelido': 'PLEN'}], 'controleAusencia': 2},
        ], actual_response[0])
        self.assertEqual(3, actual_response[1])
        self.assertEqual(
            actual_response[2], ['2', '3', '4'])

        mock_obterEventosPrevistosDeputado.assert_called_once_with(
            '123', datetime(2018, 10, 28))

    @patch("models.parlamentares.ParlamentaresApp.obterDataInicialEFinal")
    def test_obterProposicoesDeputado(
        self,
        mock_obterDataInicialEFinal,
    ):
        proposicoes = [
            {'id': '1', 'ementa': 'Teste1'},
            {'id': '2', 'ementa': 'Teste2'},
            {'id': '3', 'ementa': 'Teste3'},
        ]
        mock = Mocker(self.dep.prop)
        mock.add_response(
            "obterTodasProposicoes",
            [proposicoes],
            idAutor='123',
            dataApresentacaoInicio='2018-10-21',
            dataApresentacaoFim='2018-10-28'
        )
        mock.add_response(
            "obterAutoresProposicao",
            [{'nome': 'Fulano da Silva'}],
            "1"
        )
        mock.add_response(
            "obterAutoresProposicao",
            [{'nome': 'Sicrano'}],
            "2"
        )
        mock.add_response(
            "obterAutoresProposicao",
            [{'nome': 'Fulano da Silva'}],
            "3"
        )
        mock.add_response(
            "obterProposicao",
            proposicoes[0],
            "1"
        )
        mock.add_response(
            "obterProposicao",
            proposicoes[2],
            "3"
        )
        mock_obterDataInicialEFinal.return_value = ('2018-10-21', '2018-10-28')
        deputado = Parlamentar()
        deputado.set_id(123)
        deputado.set_nome('Fulano da Silva')

        self.dep.obterProposicoesDeputado(
            deputado, datetime(2018, 10, 28))
        actual_response = self.dep.relatorio.to_dict()['proposicoes']

        self.assertEqual(2, len(actual_response))
        self.assertEqual('Teste1', actual_response[0]['ementa'])
        self.assertEqual('Teste3', actual_response[1]['ementa'])
        mock_obterDataInicialEFinal.assert_called_once_with(
            datetime(2018, 10, 28))
        mock.assert_no_pending_responses()

    def test_obterProposicoesDeputado_fail_case(self):
        mock = Mocker(self.dep.prop)
        mock.add_exception(
            "obterTodasProposicoes",
            CamaraDeputadosError,
            idAutor="12345",
            dataApresentacaoInicio="2018-10-21",
            dataApresentacaoFim="2018-10-28"
        )
        deputado = Parlamentar()
        deputado.set_id("12345")

        self.dep.obterProposicoesDeputado(
            deputado,
            datetime(2018, 10, 28)
        )

        self.assertEqual(self.dep.relatorio.get_aviso_dados(), "Não foi possível obter proposições do parlamentar.")
        mock.assert_no_pending_responses()
