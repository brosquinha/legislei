import json
import logging
from datetime import datetime
from time import time

import pytz

from legislei.exceptions import ModelError
from legislei.houses.camara_deputados_helper import CamaraDeputadosHelper
from legislei.houses.casa_legislativa import CasaLegislativa
from legislei.models.relatorio import (Evento, Orgao, Parlamentar, Proposicao,
                                       Relatorio)
from legislei.SDKs.CamaraDeputados.entidades import (Deputados, Eventos,
                                                     Proposicoes, Votacoes)
from legislei.SDKs.CamaraDeputados.exceptions import (
    CamaraDeputadosConnectionError, CamaraDeputadosError)


class CamaraDeputadosHandler(CasaLegislativa):

    def __init__(self):
        super().__init__()
        self.dep = Deputados()
        self.relatorio = Relatorio()
        self.helper = CamaraDeputadosHelper()

    def obter_relatorio(self, parlamentar_id, data_final=None, periodo_dias=7):
        try:
            self.relatorio = Relatorio()
            self.relatorio.aviso_dados = u'Dados de votações em comissões não disponíveis.'
            start_time = time()
            if data_final:
                data_final = datetime.strptime(data_final, '%Y-%m-%d')
            else:
                data_final = datetime.now()
            logging.info('[BR1] Parlamentar: {}'.format(parlamentar_id))
            logging.info('[BR1] Data final: {}'.format(data_final))
            logging.info('[BR1] Intervalo: {}'.format(periodo_dias))
            self.set_period(periodo_dias)
            assemblyman_info = self.obter_parlamentar(parlamentar_id)
            self.relatorio.data_inicial = self.helper.get_brt(
                self.obterDataInicial(data_final, **self.periodo))
            self.relatorio.data_final = self.helper.get_brt(data_final)
            logging.info('[BR1] Deputado obtido em {0:.5f}s'.format(time() - start_time))
            events = self.helper.get_all_events(data_final)
            events_attended = self.helper.get_attended_events(events, assemblyman_info['id'])
            logging.info('[BR1] Eventos obtidos em {0:.5f}s'.format(time() - start_time))
            self.relatorio.orgaos = self.helper.get_commissions(assemblyman_info.id, data_final)
            logging.info('[BR1] Orgaos obtidos em {0:.5f}s'.format(time() - start_time))
            self._add_attended_events(events_attended)
            logging.info('[BR1] Pautas obtidas em {0:.5f}s'.format(time() - start_time))
            events_expected = self.helper.get_expected_events(self.relatorio.parlamentar.id, data_final)
            events_absent = self.helper.get_absent_events(
                events,
                events_attended,
                events_expected,
                self.relatorio.orgaos
            )
            self._add_absent_events(events_absent)
            logging.info('[BR1] Ausencias obtidas em {0:.5f}s'.format(time() - start_time))
            self.relatorio.proposicoes = self.helper.get_propositions(assemblyman_info, data_final)
            logging.info('[BR1] Proposicoes obtidas em {0:.5f}s'.format(time() - start_time))
            logging.info('[BR1] Relatorio obtido em {0:.5f}s'.format(time() - start_time))
            return self.relatorio
        except CamaraDeputadosError as event:
            logging.error("[BR1] {}".format(event))
            raise ModelError("API Câmara dos Deputados indisponível")
    
    def obter_parlamentares(self):
        deputados = []
        for page in self.dep.obterTodosDeputados():
            for item in page:
                parlamentar = Parlamentar()
                parlamentar.cargo = 'BR1'
                parlamentar.id = str(item['id'])
                parlamentar.nome = item['nome']
                parlamentar.partido = item['siglaPartido']
                parlamentar.uf = item['siglaUf']
                parlamentar.foto = item['urlFoto']
                deputados.append(parlamentar)
        return deputados

    def obter_parlamentar(self, parlamentar_id):
        try:
            deputado_info = self.dep.obterDeputado(parlamentar_id)
        except CamaraDeputadosConnectionError:
            return None
        parlamentar = Parlamentar()
        parlamentar.cargo = 'BR1'
        parlamentar.id = str(deputado_info['id'])
        parlamentar.nome = deputado_info['ultimoStatus']['nome']
        parlamentar.partido = deputado_info['ultimoStatus']['siglaPartido']
        parlamentar.uf = deputado_info['ultimoStatus']['siglaUf']
        parlamentar.foto = deputado_info['ultimoStatus']['urlFoto']
        self.relatorio.parlamentar = parlamentar
        return parlamentar
    
    def _add_attended_events(self, events_attended):
        """
        Adds given attended events to report

        :param events_attended: List of events attended by assemblyman
        :type events_attended: List[Evento]
        :rtype: None
        """
        for event in events_attended:
            event.set_presente()
            program = self.helper.get_event_program(event.id)
            if program == [{'error': True}]:
                # TODO Schema error fields
                self.relatorio.eventos_presentes.append(event)
                continue
            for item in program:
                self._get_program_propositions(item, event)
            self.relatorio.eventos_presentes.append(event)

    def _get_program_propositions(self, item, event):
        if item['proposicao_detalhes'] == [{'error': True}]:
            # TODO Schema error fields
            return
        proposition = self.helper.build_proposition(item['proposicao_detalhes'])
        vote, voting_agenda = self.helper.get_votes(
            self.relatorio.parlamentar.id,
            proposition={
                'tipo': proposition.tipo,
                'numero': proposition.numero,
                'ano': item['proposicao_detalhes']['ano']
            },
            event_dates={
                'data_inicial': event.data_inicial,
                'data_final': event.data_final,
            }
        )
        proposition.voto = vote if vote else "ERROR"
        if voting_agenda:
            proposition.pauta = '{} de {}'.format(
                voting_agenda, proposition.pauta)
        event.pautas.append(proposition)
    
    def _add_absent_events(self, absent_events):
        """
        Adds given absent events to report

        :param absent_events: List of absent events
        :type absent_event: List[Evento]
        :rtype: None
        """
        for event in absent_events:
            self.relatorio.eventos_ausentes.append(event)
            if event.presenca > 1:
                self.relatorio.eventos_previstos.append(event)
        self.relatorio.eventos_ausentes_esperados_total = len(self.relatorio.eventos_previstos)
