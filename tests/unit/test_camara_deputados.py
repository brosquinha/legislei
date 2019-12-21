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

    def test_add_attended_events(self):
        events_attended = [
            Evento(
                id='3',
                data_inicial=self.dep.helper.get_brt(datetime(2019, 12, 10)),
                data_final=self.dep.helper.get_brt(datetime(2019, 12, 17))
            ),
            Evento(
                id='4',
                data_inicial=self.dep.helper.get_brt(datetime(2019, 12, 10)),
                data_final=self.dep.helper.get_brt(datetime(2019, 12, 17))
            )
        ]
        mock_ev = Mocker(self.dep.helper.ev)
        mock_prop = Mocker(self.dep.helper.prop)
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

        self.dep._add_attended_events(events_attended)

        self.assertEqual(self.dep.relatorio.eventos_presentes, [
            Evento(
                id='3',
                data_inicial=self.dep.helper.get_brt(datetime(2019, 12, 10)),
                data_final=self.dep.helper.get_brt(datetime(2019, 12, 17)),
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
                data_inicial=self.dep.helper.get_brt(datetime(2019, 12, 10)),
                data_final=self.dep.helper.get_brt(datetime(2019, 12, 17)),
                presenca=0,
                pautas=[]
            )
        ])

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

        self.dep._add_absent_events(absent_events)

        self.assertEqual(self.dep.relatorio.eventos_ausentes, absent_events)
        absent_events.pop(2)
        self.assertEqual(self.dep.relatorio.eventos_previstos, absent_events)
        self.assertEqual(self.dep.relatorio.eventos_ausentes_esperados_total, 3)
