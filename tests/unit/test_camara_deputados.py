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

    def test_obter_parlamentares(self):
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
                cargo='BR1'
            ),
            Parlamentar(
                nome='FULANO PESSOA',
                id='2',
                partido='P2',
                uf='UF',
                foto='foto2',
                cargo='BR1'
            ),
            Parlamentar(
                nome='SICRANO PINTO',
                id='3',
                partido='P1',
                uf='UF2',
                foto='foto3',
                cargo='BR1'
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
    def test_get_commissions(
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

        actual_response = self.dep.get_commissions(
            '1234', datetime(2018, 10, 28))

        self.assertIn(Orgao(nome='Comissão A'), actual_response)
        self.assertIn(Orgao(nome='Comissão C'), actual_response)
        self.assertEqual(len(actual_response), 2)

        mock.assert_no_pending_responses()
        mock_obterDataInicialEFinal.assert_called_once_with(
            datetime(2018, 10, 28))

    def test_get_commissions_fail_case(self):
        mock = Mocker(self.dep.dep)
        mock.add_exception('obterOrgaosDeputado', CamaraDeputadosError('teste'))

        actual_response = self.dep.get_commissions('1234', datetime(2018, 10, 28))

        self.assertEqual(actual_response, [{'nomeOrgao': None}])
        mock.assert_no_pending_responses()

    @patch("legislei.houses.camara_deputados.CamaraDeputadosHandler.obterDataInicialEFinal")
    def test_get_all_events(
            self,
            mock_obterDataInicialEFinal
    ):
        mock = Mocker(self.dep.ev)
        mock.add_response(
            "obterTodosEventos",
            [
                [
                    {
                        'id': '123',
                        'dataHoraInicio': '2018-10-24T10:00',
                        'dataHoraFim': '2018-10-24T12:00',
                        'situacao': 'Encerrada',
                        'descricao': 'Sessão Ordinária',
                        'uri': 'uri',
                        'orgaos': [
                            {'nome': 'Plenário', 'apelido': 'PLEN'}
                        ]
                    },
                    {
                        'id': '1234',
                        'dataHoraInicio': '2018-10-24T14:00',
                        'dataHoraFim': '2018-10-24T18:45',
                        'situacao': 'Encerrada',
                        'descricao': 'Sessão Extraordinária',
                        'uri': 'uri',
                        'orgaos': [
                            {'nome': 'Plenário', 'apelido': 'PLEN'}
                        ]
                    }
                ],
                [
                    {
                        'id': '12345',
                        'dataHoraInicio': '2018-10-25T10:00',
                        'dataHoraFim': None,
                        'situacao': 'Cancelada',
                        'descricao': 'Sessão Ordinária',
                        'uri': 'uri',
                        'orgaos': [
                            {'nome': 'Comissão de Constituição e Justiça', 'apelido': 'CCJ'}
                        ]
                    }
                ]
            ],
            dataInicio='2018-10-21', dataFim='2018-10-28'
        )
        mock_obterDataInicialEFinal.return_value = ('2018-10-21', '2018-10-28')

        actual_response = self.dep.get_all_events(datetime(2018, 10, 28))

        self.assertEqual([
            Evento(
                id='123',
                data_inicial=self.dep._get_brt(datetime(2018, 10, 24, 10, 0)),
                data_final=self.dep._get_brt(datetime(2018, 10, 24, 12, 0)),
                situacao='Encerrada',
                nome='Sessão Ordinária',
                url='uri',
                orgaos=[
                    Orgao(nome='Plenário', apelido='PLEN')
                ]
            ),
            Evento(
                id='1234',
                data_inicial=self.dep._get_brt(datetime(2018, 10, 24, 14, 0)),
                data_final=self.dep._get_brt(datetime(2018, 10, 24, 18, 45)),
                situacao='Encerrada',
                nome='Sessão Extraordinária',
                url='uri',
                orgaos=[
                    Orgao(nome='Plenário', apelido='PLEN')
                ]
            ),
            Evento(
                id='12345',
                data_inicial=self.dep._get_brt(datetime(2018, 10, 25, 10, 0)),
                data_final=None,
                situacao='Cancelada',
                nome='Sessão Ordinária',
                url='uri',
                orgaos=[
                    Orgao(nome='Comissão de Constituição e Justiça', apelido='CCJ')
                ]
            ),
        ], actual_response)

        mock_obterDataInicialEFinal.assert_called_once_with(
            datetime(2018, 10, 28))
        mock.assert_no_pending_responses()

    def test_build_event(self):
        event = {
            'id': '123',
            'dataHoraInicio': '2019-08-10T10:00',
            'dataHoraFim': '2019-08-10T12:00',
            'situacao': 'Encerrada',
            'descricao': 'Sessão Ordinária',
            'uri': 'uri',
            'orgaos': [
                {'nome': 'Plenário', 'apelido': 'PLEN'}
            ]
        }
        expected = Evento(
            id='123',
            data_inicial=self.dep._get_brt(datetime(2019, 8, 10, 10)),
            data_final=self.dep._get_brt(datetime(2019, 8, 10, 12)),
            situacao='Encerrada',
            nome='Sessão Ordinária',
            url='uri',
            orgaos=[
                Orgao(nome='Plenário', apelido='PLEN')
            ]
        )

        actual = self.dep.build_event(event)

        self.assertEqual(expected, actual)

    def test_get_attended_events(self):
        mock = Mocker(self.dep.ev)
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
        events = [
            {'id': '123'},
            {'id': '1234'},
            {'id': '12345'}
        ]
        dep_id = '12345'

        actual_response = self.dep.get_attended_events(events, dep_id)

        self.assertEqual([
            {'id': '123'}, {'id': '12345'}
        ], actual_response)

        mock.assert_no_pending_responses()

    @patch("legislei.houses.camara_deputados.CamaraDeputadosHandler.obterDataInicialEFinal")
    def test_get_expected_events(
            self,
            mock_obterDataInicialEFinal,
    ):
        events = [
            {'id': 1, 'descricao': 'Evento 1'},
            {'id': 2, 'descricao': 'Evento 2'},
            {'id': 3, 'descricao': 'Evento 3'}
        ]
        dep_id = '12345'
        mock = Mocker(self.dep.dep)
        mock.add_response(
            "obterEventosDeputado",
            [events],
            dep_id,
            dataInicio='2018-10-21',
            dataFim='2018-10-28'
        )

        mock_obterDataInicialEFinal.return_value = ('2018-10-21', '2018-10-28')

        actual_response = self.dep.get_expected_events(
            dep_id, datetime(2018, 10, 28))

        self.assertEqual(actual_response, [
            Evento(id='1', nome='Evento 1'),
            Evento(id='2', nome='Evento 2'),
            Evento(id='3', nome='Evento 3'),
        ])

        mock_obterDataInicialEFinal.assert_called_once_with(
            datetime(2018, 10, 28))
        mock.assert_no_pending_responses()

    def test_get_expected_events_fail_case(self):
        mock = Mocker(self.dep.dep)
        mock.add_exception("obterEventosDeputado", CamaraDeputadosError)

        actual_response = self.dep.get_expected_events("123", datetime(2018, 10, 28))

        self.assertEqual(actual_response, [{'id': None}])
        mock.assert_no_pending_responses()

    def test_get_event_program(
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

        actual_response = self.dep.get_event_program(ev_id)

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

    def test_get_event_program_fail_case(self):
        mock = Mocker(self.dep.ev)
        mock.add_exception("obterPautaEvento", CamaraDeputadosError, "12345")

        actual_response = self.dep.get_event_program("12345")

        self.assertEqual(actual_response, [{'error': True}])
        mock.assert_no_pending_responses()

    def test_get_event_program_program_none(self):
        mock = Mocker(self.dep.ev)
        mock.add_response("obterPautaEvento", None, "12345")

        actual_response = self.dep.get_event_program("12345")

        self.assertEqual(actual_response, [])
        mock.assert_no_pending_responses()

    def test_get_votes(
            self,
    ):
        votings = [
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
            votings
        )

        actual_response = self.dep.get_votes(
            '12345',
            proposition={
                'tipo': 'PL',
                'numero': '1',
                'ano': '2019'
            },
            event_dates={
                'data_inicial': datetime(2019, 5, 12, 10),
                'data_final': datetime(2019, 5, 12, 14)
            }
        )

        self.assertEqual(('Sim', 'Votação 1'), actual_response)
        mock.assert_no_pending_responses()

    def test_get_votes_fail_case(self):
        mock = Mocker(self.dep.prop)
        mock.add_exception("obterVotacoesProposicao", CamaraDeputadosError)

        actual_response = self.dep.get_votes(
            '12345',
            proposition={
                'tipo': 'PL',
                'numero': '1',
                'ano': '2019'
            },
            event_dates={
                'data_inicial': datetime(2019, 5, 12, 10),
                'data_final': datetime(2019, 5, 12, 14)
            }
        )

        self.assertIsNone(actual_response[0])
        self.assertIsNone(actual_response[1])
        mock.assert_no_pending_responses()

    def test_add_attended_events(self):
        events_attended = [
            Evento(
                id='3',
                data_inicial=datetime(2019, 12, 10),
                data_final=datetime(2019, 12, 17)
            ),
            Evento(
                id='4',
                data_inicial=datetime(2019, 12, 10),
                data_final=datetime(2019, 12, 17)
            )
        ]
        mock_ev = Mocker(self.dep.ev)
        mock_prop = Mocker(self.dep.prop)
        mock_ev.add_response("obterPautaEvento", [
                {
                    'codRegime': '123',
                    'proposicao_': {
                        'id': '11'
                    }
                },
                {
                    'codRegime': '123',
                    'proposicao_': {
                        'id': '12'
                    }
                },
            ])
        mock_ev.add_exception("obterPautaEvento", CamaraDeputadosError)
        mock_prop.add_response("obterProposicao", {
            'id': '11',
            'nome': 'Proposição I',
            'ementa': 'Proposição I',
            'numero': '11',
            'ano': 2019
            })
        mock_prop.add_exception("obterProposicao", CamaraDeputadosError)
        mock_prop.add_response("obterVotacoesProposicao", [{
                'data': '15/12/2019',
                'hora': '12:00',
                'resumo': 'Votação 1',
                'votos': [
                    {'id': '23456', 'voto': 'Não'},
                    {'id': '12345', 'voto': 'Sim'},
                    {'id': '34567', 'voto': 'Abstenção'},
                ]
            }])
        mock_prop.add_response("obterVotacoesProposicao", [{
                'data': '16/12/2019',
                'hora': '12:00',
                'resumo': 'Votação 2',
                'votos': [
                    {'id': '23456', 'voto': 'Sim'},
                    {'id': '12345', 'voto': 'Não'},
                    {'id': '34567', 'voto': 'Abstenção'},
                ]
            }])
        self.dep.relatorio = Relatorio(
            parlamentar=Parlamentar(id='12345')
        )

        self.dep.add_attended_events(events_attended)

        self.assertEqual(self.dep.relatorio.eventos_presentes, [
            Evento(
                id='3',
                data_inicial=datetime(2019, 12, 10),
                data_final=datetime(2019, 12, 17),
                presenca=0,
                pautas=[
                    Proposicao(
                        id='11',
                        numero='11',
                        ementa='Proposição I',
                        pauta='Votação 1 de Proposição I',
                        voto='Sim'
                    )
                ]
            ),
            Evento(
                id='4',
                data_inicial=datetime(2019, 12, 10),
                data_final=datetime(2019, 12, 17),
                presenca=0,
                pautas=[]
            )
        ])

    def test_get_absent_events(self):
        expected_events = [self.dep.build_event(e) for e in
            [
                {'id': '2'},
                {'id': '3'},
                {'id': '4'},
            ]
        ]
        events = [self.dep.build_event(e) for e in [
                {'id': '1', 'orgaos': [{'nome': 'Órgão 1', 'apelido': ''}]},
                {'id': '2', 'orgaos': [{'nome': 'Órgão 1', 'apelido': ''}]},
                {'id': '3', 'orgaos': [{'nome': 'Órgão 2', 'apelido': ''}]},
                {'id': '4', 'orgaos': [{'nome': 'Órgão 2', 'apelido': ''}]},
                {'id': '5', 'orgaos': [{'nome': 'Órgão 4', 'apelido': ''}]},
                {'id': '6', 'orgaos': [{'nome': 'Órgão 4', 'apelido': 'PLEN'}]},
            ]
        ]
        events_attended = [self.dep.build_event(e) for e in [
                {'id': '3', 'orgaos': [{'nome': 'Órgão 2', 'apelido': ''}]},
                {'id': '4', 'orgaos': [{'nome': 'Órgão 2', 'apelido': ''}]},
            ]
        ]
        commissions = [
            {'nomeOrgao': 'Órgão 1'},
            {'nomeOrgao': 'Órgão 2'},
            {'nomeOrgao': 'Órgão 3'}
        ]

        actual_response = self.dep.get_absent_events(
            events,
            events_attended,
            expected_events,
            commissions,
        )

        self.assertEqual([
            Evento(
                id='1', presenca=2, orgaos=[Orgao(nome='Órgão 1', apelido='')]
            ),
            Evento(
                id='2', presenca=3, orgaos=[Orgao(nome='Órgão 1', apelido='')]
            ),
            Evento(
                id='5', presenca=1, orgaos=[Orgao(nome='Órgão 4', apelido='')]
            ),
            Evento(
                id='6', presenca=2, orgaos=[Orgao(nome='Órgão 4', apelido='PLEN')]
            ),
        ], actual_response)

    def test_add_absent_events(self):
        absent_events = [
            Evento(
                id='1', presenca=2, orgaos=[Orgao(nome='Órgão 1', apelido='')]
            ),
            Evento(
                id='2', presenca=3, orgaos=[Orgao(nome='Órgão 1', apelido='')]
            ),
            Evento(
                id='5', presenca=1, orgaos=[Orgao(nome='Órgão 4', apelido='')]
            ),
            Evento(
                id='6', presenca=2, orgaos=[Orgao(nome='Órgão 4', apelido='PLEN')]
            ),
        ]
        self.dep.relatorio = Relatorio()

        self.dep.add_absent_events(absent_events)

        self.assertEqual(self.dep.relatorio.eventos_ausentes, absent_events)
        absent_events.pop(2)
        self.assertEqual(self.dep.relatorio.eventos_previstos, absent_events)
        self.assertEqual(self.dep.relatorio.eventos_ausentes_esperados_total, 3)

    @patch("legislei.houses.camara_deputados.CamaraDeputadosHandler.obterDataInicialEFinal")
    def test_get_propositions(
        self,
        mock_obterDataInicialEFinal,
    ):
        propositions = [
            {'id': '1', 'ementa': 'Teste1'},
            {'id': '2', 'ementa': 'Teste2'},
            {'id': '3', 'ementa': 'Teste3'},
        ]
        mock = Mocker(self.dep.prop)
        mock.add_response(
            "obterTodasProposicoes",
            [propositions],
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
            propositions[0],
            "1"
        )
        mock.add_response(
            "obterProposicao",
            propositions[2],
            "3"
        )
        mock_obterDataInicialEFinal.return_value = ('2018-10-21', '2018-10-28')
        assemblyman = Parlamentar()
        assemblyman.id = '123'
        assemblyman.nome = 'Fulano da Silva'
        self.dep.relatorio.parlamentar = assemblyman
        self.dep.relatorio.data_inicial = datetime(2018, 10, 21)
        self.dep.relatorio.data_final = datetime(2018, 10, 28)

        self.dep.get_propositions(
            assemblyman, datetime(2018, 10, 28))
        actual_response = self.dep.relatorio.to_dict()['proposicoes']

        self.assertEqual(2, len(actual_response))
        self.assertEqual('Teste1', actual_response[0]['ementa'])
        self.assertEqual('Teste3', actual_response[1]['ementa'])
        mock_obterDataInicialEFinal.assert_called_once_with(
            datetime(2018, 10, 28))
        mock.assert_no_pending_responses()

    def test_get_propositions_fail_case(self):
        mock = Mocker(self.dep.prop)
        mock.add_exception(
            "obterTodasProposicoes",
            CamaraDeputadosError,
            idDeputadoAutor="12345",
            dataApresentacaoInicio="2018-10-21",
            dataApresentacaoFim="2018-10-28"
        )
        assemblyman = Parlamentar()
        assemblyman.id = "12345"

        self.dep.get_propositions(
            assemblyman,
            datetime(2018, 10, 28)
        )

        self.assertEqual(self.dep.relatorio.aviso_dados, "Não foi possível obter proposições do parlamentar.")
        mock.assert_no_pending_responses()

    def test_build_proposition(self):
        proposition = {
            'id': 123,
            'dataApresentacao': '2018-10-25T00:00',
            'ementa': 'Dá nova redação ao artigo tal da Constituição Federal',
            'numero': 14,
            'ano': 2019,
            'siglaTipo': 'PEC',
            'urlInteiroTeor': 'http://www.camara.gov.br/proposicoesWeb/prop_mostrarintegra?codteor=141414',
            'uriAutores': 'https://dadosabertos.camara.leg.br/api/v2/proposicoes/123/autores'
        }
        expected = Proposicao(
            id='123',
            data_apresentacao=self.dep._get_brt(datetime(2018, 10, 25)),
            ementa=proposition['ementa'],
            numero='14',
            tipo='PEC',
            url_documento=proposition['urlInteiroTeor'],
            url_autores=proposition['uriAutores'],
            pauta=proposition['ementa']
        )

        actual = self.dep.build_proposition(proposition)

        self.assertEqual(expected, actual)

