import json
import logging
import unittest
from datetime import datetime
from unittest.mock import patch

from legislei.houses.camara_deputados import CamaraDeputadosHandler
from legislei.models.relatorio import (Evento, Orgao, Parlamentar, Proposicao,
                                       Relatorio)
from legislei.SDKs.CamaraDeputados.entidades import Deputados
from legislei.SDKs.CamaraDeputados.exceptions import (
    CamaraDeputadosConnectionError, CamaraDeputadosError)
from legislei.SDKs.CamaraDeputados.mock import Mocker


class TestCamaraDeputadosHandler(unittest.TestCase):

    def setUp(self):
        self.dep = CamaraDeputadosHandler()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_obterParlamentares(self):
        def fakeObterDeputados():
            yield [
                {
                    'nome': 'CESAR DA SILVA',
                    'id': '1',
                    'siglaPartido': 'P1',
                    'siglaUf': 'UF',
                    'urlFoto': 'foto',
                },
                {
                    'nome': 'FULANO PESSOA',
                    'id': '2',
                    'siglaPartido': 'P2',
                    'siglaUf': 'UF',
                    'urlFoto': 'foto2',
                }
            ]
            yield [
                {
                    'nome': 'SICRANO PINTO',
                    'id': '3',
                    'siglaPartido': 'P1',
                    'siglaUf': 'UF2',
                    'urlFoto': 'foto3',
                }
            ]
        expected = [
            Parlamentar(
                nome='CESAR DA SILVA',
                id='1',
                partido='P1',
                uf='UF',
                foto='foto',
            ),
            Parlamentar(
                nome='FULANO PESSOA',
                id='2',
                partido='P2',
                uf='UF',
                foto='foto2',
            ),
            Parlamentar(
                nome='SICRANO PINTO',
                id='3',
                partido='P1',
                uf='UF2',
                foto='foto3',
            )
        ]
        mock = Mocker(self.dep.dep)
        mock.add_response('obterTodosDeputados', fakeObterDeputados())
        actual_response = self.dep.obter_parlamentares()
        self.assertEqual(actual_response, expected)

    def test_obter_parlamentar_success(self):
        expected = Parlamentar(
            nome='CESAR DA SILVA',
            id='1',
            partido='P1',
            uf='UF',
            foto='foto',
            cargo='BR1'
        )
        mock = Mocker(self.dep.dep)
        mock.add_response('obterDeputado', {
            'id': '1',
            'ultimoStatus': {
                'nome': 'CESAR DA SILVA',
                'siglaPartido': 'P1',
                'siglaUf': 'UF',
                'urlFoto': 'foto'
            }
        })

        actual_response = self.dep.obter_parlamentar("1")

        self.assertEqual(actual_response, expected)

    def test_obter_parlamentar_invalid_id(self):
        mock = Mocker(self.dep.dep)
        mock.add_exception('obterDeputado', CamaraDeputadosConnectionError("url", 400))

        actual_response = self.dep.obter_parlamentar("invalid")

        self.assertIsNone(actual_response)

    @patch("legislei.houses.camara_deputados.CamaraDeputadosHandler.obterDataInicialEFinal")
    def test_obterOrgaosDeputado(
            self,
            mock_obterDataInicialEFinal
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
            dataInicio='2018-10-21',
            dataFim='2018-10-28'
        )
        mock_obterDataInicialEFinal.return_value = ('2018-10-21', '2018-10-28')

        actual_response = self.dep.obterOrgaosDeputado(
            '1234', datetime(2018, 10, 28))

        self.assertIn({'nomeOrgao': 'Comissão A', 'dataFim': None}, actual_response)
        self.assertIn(
            {'nomeOrgao': 'Comissão C', 'dataFim': '2018-12-31'}, actual_response)
        self.assertEqual(len(actual_response), 2)

        mock.assert_no_pending_responses()
        mock_obterDataInicialEFinal.assert_called_once_with(
            datetime(2018, 10, 28))

    def test_obterOrgaosDeputado_fail_case(self):
        mock = Mocker(self.dep.dep)
        mock.add_exception('obterOrgaosDeputado', CamaraDeputadosError)

        actual_response = self.dep.obterOrgaosDeputado('1234', datetime(2018, 10, 28))

        self.assertEqual(actual_response, [{'nomeOrgao': None}])
        mock.assert_no_pending_responses()

    @patch("legislei.houses.camara_deputados.CamaraDeputadosHandler.obterDataInicialEFinal")
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

    @patch("legislei.houses.camara_deputados.CamaraDeputadosHandler.obterDataInicialEFinal")
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

        actual_response = self.dep.obterPautaEvento(ev_id)

        self.assertEqual(actual_response, [
            {
                'codRegime': '123',
                'proposicao_': {
                    'id': '12345'
                },
                'proposicao_detalhes': {'nome': 'Proposição I'}
            },
            {
                'codRegime': '987',
                'proposicao_': {
                    'id': '98765'
                },
                'proposicao_detalhes': {'nome': 'Proposição II'}
            },
            {
                'codRegime': '987',
                'proposicao_': {
                    'id': '56789'
                },
                'proposicao_detalhes': [{'error': True}]
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
        votacoes = [
            {
                'data': '12/5/2019',
                'hora': '12:00',
                'resumo': 'Votação 1',
                'votos': [
                    {'id': '23456', 'voto': 'Não'},
                    {'id': '12345', 'voto': 'Sim'},
                    {'id': '34567', 'voto': 'Abstenção'},
                ]
            },
            {
                'data': '12/5/2019',
                'hora': '18:00',
                'resumo': 'Votação 2',
                'votos': [
                    {'id': '23456', 'voto': 'Sim'},
                    {'id': '12345', 'voto': 'Não'},
                    {'id': '34567', 'voto': 'Obstrução'},
                ]
            },
        ]
        mock = Mocker(self.dep.prop)
        mock.add_response(
            "obterVotacoesProposicao",
            votacoes
        )

        actual_response = self.dep.obterVotoDeputado(
            '12345',
            proposicao={
                'tipo': 'PL',
                'numero': '1',
                'ano': '2019'
            },
            datas_evento={
                'data_inicial': datetime(2019, 5, 12, 10),
                'data_final': datetime(2019, 5, 12, 14)
            }
        )

        self.assertEqual(('Sim', 'Votação 1'), actual_response)
        mock.assert_no_pending_responses()

    def test_obterVotoDeputado_fail_case(self):
        mock = Mocker(self.dep.prop)
        mock.add_exception("obterVotacoesProposicao", CamaraDeputadosError)

        actual_response = self.dep.obterVotoDeputado(
            '12345',
            proposicao={
                'tipo': 'PL',
                'numero': '1',
                'ano': '2019'
            },
            datas_evento={
                'data_inicial': datetime(2019, 5, 12, 10),
                'data_final': datetime(2019, 5, 12, 14)
            }
        )

        self.assertIsNone(actual_response[0])
        self.assertIsNone(actual_response[1])
        mock.assert_no_pending_responses()

    @patch("legislei.houses.camara_deputados.CamaraDeputadosHandler.obterEventosPrevistosDeputado")
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

    @patch("legislei.houses.camara_deputados.CamaraDeputadosHandler.obterDataInicialEFinal")
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
            idDeputadoAutor='123',
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
        deputado.id = '123'
        deputado.nome = 'Fulano da Silva'
        self.dep.relatorio.parlamentar = deputado
        self.dep.relatorio.data_inicial = datetime(2018, 10, 21)
        self.dep.relatorio.data_final = datetime(2018, 10, 28)

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
            idDeputadoAutor="12345",
            dataApresentacaoInicio="2018-10-21",
            dataApresentacaoFim="2018-10-28"
        )
        deputado = Parlamentar()
        deputado.id = "12345"

        self.dep.obterProposicoesDeputado(
            deputado,
            datetime(2018, 10, 28)
        )

        self.assertEqual(self.dep.relatorio.aviso_dados, "Não foi possível obter proposições do parlamentar.")
        mock.assert_no_pending_responses()
