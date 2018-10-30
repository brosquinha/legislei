import json
import unittest
from datetime import datetime
from unittest.mock import patch
from SDKs.CamaraDeputados.entidades import Deputados
from deputados import DeputadosApp


class TestDeputadosApp(unittest.TestCase):

    def setUp(self):
        self.dep = DeputadosApp()

    @patch("SDKs.CamaraDeputados.entidades.Deputados.obterTodosDeputados")
    def test_obterDeputados(self, mock_obterTodosDeputados):
        def fakeObterDeputados():
            yield [{'nome': 'CESAR DA SILVA'}, {'nome': 'FULANO PESSOA'}]
            yield [{'nome': 'SICRANO PINTO'}]
        mock_obterTodosDeputados.side_effect = fakeObterDeputados
        actual_response = self.dep.obterDeputados()
        mock_obterTodosDeputados.assert_any_call()
        self.assertEqual(actual_response[0], json.dumps([
            {'nome': 'CESAR DA SILVA'},
            {'nome': 'FULANO PESSOA'},
            {'nome': 'SICRANO PINTO'}
        ]))

    @patch("SDKs.CamaraDeputados.entidades.Deputados.obterOrgaosDeputado")
    @patch("parlamentares.ParlamentaresApp.formatarDatasYMD")
    @patch("parlamentares.ParlamentaresApp.obterDataInicial")
    def test_obterOrgaosDeputado(
            self,
            mock_obterDataInicial,
            mock_formatarDatasYMD,
            mock_obterOrgaosDeputado
    ):
        def fakeObterOrgaosDeputado(*args, **kwargs):
            yield [
                {'nome': 'Comissão A', 'dataFim': None},
                {'nome': 'Comissão B', 'dataFim': '2018-08-31'}
            ]
            yield [
                {'nome': 'Comissão C', 'dataFim': '2018-12-31'}
            ]
        mock_obterDataInicial.return_value = datetime(2018, 10, 21)
        mock_formatarDatasYMD.return_value = ('2018-10-21')
        mock_obterOrgaosDeputado.side_effect = fakeObterOrgaosDeputado

        actual_response = self.dep.obterOrgaosDeputado(
            '1234', datetime(2018, 10, 28))

        self.assertIn({'nome': 'Comissão A', 'dataFim': None}, actual_response)
        self.assertIn(
            {'nome': 'Comissão C', 'dataFim': '2018-12-31'}, actual_response)
        self.assertEqual(len(actual_response), 2)

        mock_obterDataInicial.assert_called_once_with(
            datetime(2018, 10, 28), weeks=1)
        mock_obterOrgaosDeputado.assert_called_with(
            '1234', dataInicial='2018-10-21')
        mock_formatarDatasYMD.assert_called_once_with(datetime(2018, 10, 21))

    @patch("SDKs.CamaraDeputados.entidades.Eventos.obterDeputadosEvento")
    @patch("SDKs.CamaraDeputados.entidades.Eventos.obterTodosEventos")
    @patch("parlamentares.ParlamentaresApp.obterDataInicialEFinal")
    def test_procurarEventosComDeputado(
            self,
            mock_obterDataInicialEFinal,
            mock_obterTodosEventos,
            mock_obterDeputadosEvento
    ):
        def fakeObterTodosEventos(**kwargs):
            yield [{'id': '123'}, {'id': '1234'}]
            yield [{'id': '12345'}]

        def fakeObterDeputadosEvento(id):
            if id != '1234':
                return [{'id': '12345'}, {'id': '98765'}]
            return [{'id': '98765'}, {'id': '34567'}]
        mock_obterDataInicialEFinal.return_value = ('2018-10-21', '2018-10-28')
        mock_obterTodosEventos.side_effect = fakeObterTodosEventos
        mock_obterDeputadosEvento.side_effect = fakeObterDeputadosEvento
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
        mock_obterTodosEventos.assert_called_with(
            dataInicio='2018-10-21', dataFim='2018-10-28')
        mock_obterDeputadosEvento.assert_called_with(dep_id)

    @patch("SDKs.CamaraDeputados.entidades.Deputados.obterEventosDeputado")
    @patch("parlamentares.ParlamentaresApp.obterDataInicialEFinal")
    def test_obterEventosPrevistosDeputado(
            self,
            mock_obterDataInicialEFinal,
            mock_obterEventosDeputado
    ):
        eventos = [
            {'nome': 'Evento 1'},
            {'nome': 'Evento 2'},
            {'nome': 'Evento 3'}
        ]
        dep_id = '12345'

        def fakeObterEventosDeputado(*args, **kwargs):
            yield eventos[0:2]
            yield eventos[2:]
        mock_obterDataInicialEFinal.return_value = ('2018-10-21', '2018-10-28')
        mock_obterEventosDeputado.side_effect = fakeObterEventosDeputado

        actual_response = self.dep.obterEventosPrevistosDeputado(
            dep_id, datetime(2018, 10, 28))

        self.assertEqual(eventos, actual_response)

        mock_obterDataInicialEFinal.assert_called_once_with(
            datetime(2018, 10, 28))
        mock_obterEventosDeputado.assert_called_with(
            dep_id,
            dataInicio='2018-10-21',
            dataFim='2018-10-28'
        )

    @patch("SDKs.CamaraDeputados.entidades.Proposicoes.obterVotacoesProposicao")
    @patch("SDKs.CamaraDeputados.entidades.Proposicoes.obterProposicao")
    @patch("SDKs.CamaraDeputados.entidades.Eventos.obterPautaEvento")
    def test_obterPautaEvento(
            self,
            mock_obterPautaEvento,
            mock_obterProposicao,
            mock_obterVotacoesProposicao
    ):
        def fakeObterProposicao(id):
            if id == '12345':
                return {'nome': 'Proposição I'}
            return {'nome': 'Proposição II'}
        ev_id = '1234'
        mock_obterPautaEvento.return_value = [
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
        ]
        mock_obterProposicao.side_effect = fakeObterProposicao
        mock_obterVotacoesProposicao.return_value = {'votos': '512'}

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
                'votacao': {'votos': '512'}
            },
        ])

        mock_obterPautaEvento.assert_called_once_with(ev_id)

    @patch("SDKs.CamaraDeputados.entidades.Votacoes.obterVotos")
    def test_obterVotoDeputado(
            self,
            mock_obterVotos
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

        def fakeObterVotos(*args, **kwargs):
            yield votos[0:2]
            yield votos[2:]
        mock_obterVotos.side_effect = fakeObterVotos

        actual_response = self.dep.obterVotoDeputado('', '12345')

        self.assertEqual('Sim', actual_response)

    @patch("deputados.DeputadosApp.obterEventosPrevistosDeputado")
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

        mock_obterEventosPrevistosDeputado.assert_called_once_with(
            '123', datetime(2018, 10, 28))

    @patch("SDKs.CamaraDeputados.entidades.Proposicoes.obterProposicao")
    @patch("SDKs.CamaraDeputados.entidades.Proposicoes.obterTodasProposicoes")
    @patch("parlamentares.ParlamentaresApp.obterDataInicialEFinal")
    def test_obterProposicoesDeputado(
        self,
        mock_obterDataInicialEFinal,
        mock_obterTodasProposicoes,
        mock_obterProposicao
    ):
        def fakeObterTodasProposicoes(*args, **kwargs):
            yield proposicoes[0:2]
            yield proposicoes[2:]
        def fakeObterProposicao(*arg, **kwargs):
            return proposicoes[int(arg[0]) - 1]
        mock_obterDataInicialEFinal.return_value = ('2018-10-21', '2018-10-28')
        proposicoes = [
            {'id': '1'},
            {'id': '2'},
            {'id': '3'},
        ]
        mock_obterTodasProposicoes.side_effect = fakeObterTodasProposicoes
        mock_obterProposicao.side_effect = fakeObterProposicao

        actual_response = self.dep.obterProposicoesDeputado(
            '123', datetime(2018, 10, 28))

        self.assertEqual(actual_response, proposicoes)

        mock_obterDataInicialEFinal.assert_called_once_with(
            datetime(2018, 10, 28))
        mock_obterTodasProposicoes.assert_called_with(
            idAutor='123',
            dataApresentacaoInicio='2018-10-21',
            dataApresentacaoFim='2018-10-28'
        )
