import json
import logging
from datetime import datetime
from time import time

import pytz
from flask import render_template, request

from legislei.exceptions import ModelError
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
        self.ev = Eventos()
        self.prop = Proposicoes()
        self.vot = Votacoes()
        self.relatorio = Relatorio()
        self.brasilia_tz = pytz.timezone('America/Sao_Paulo')

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
            self.relatorio.data_inicial = self._get_brt(
                self.obterDataInicial(data_final, **self.periodo))
            self.relatorio.data_final = self._get_brt(data_final)
            logging.info('[BR1] Deputado obtido em {0:.5f}s'.format(time() - start_time))
            events = self.get_all_events(data_final)
            events_attended = self.get_attended_events(events, assemblyman_info['id'])
            logging.info('[BR1] Eventos obtidos em {0:.5f}s'.format(time() - start_time))
            self.relatorio.orgaos = self.get_commissions(assemblyman_info.id, data_final)
            logging.info('[BR1] Orgaos obtidos em {0:.5f}s'.format(time() - start_time))
            self.add_attended_events(events_attended)
            logging.info('[BR1] Pautas obtidas em {0:.5f}s'.format(time() - start_time))
            events_expected = self.get_expected_events(self.relatorio.parlamentar.id, data_final)
            events_absent = self.get_absent_events(
                events,
                events_attended,
                events_expected,
                self.relatorio.orgaos
            )
            self.add_absent_events(events_absent)
            logging.info('[BR1] Ausencias obtidas em {0:.5f}s'.format(time() - start_time))
            self.get_propositions(assemblyman_info, data_final)
            logging.info('[BR1] Proposicoes obtidas em {0:.5f}s'.format(time() - start_time))
            logging.info('[BR1] Relatorio obtido em {0:.5f}s'.format(time() - start_time))
            return self.relatorio
        except CamaraDeputadosError as event:
            logging.error("[BR1] {}".format(event))
            raise ModelError("API Câmara dos Deputados indisponível")

    def get_commissions(self, assemblyman_id, final_date):
        """
        Gets all commissions assemblyman is member of in the report period

        :param assemblyman_id: Assemblyman id
        :type assemblyman_id: String
        :param final_date: Report period final date
        :type final_date: Datetime
        :return: List of commissions
        :rtype: List[Orgao]
        """
        commissions = []
        di, df = self.obterDataInicialEFinal(final_date)
        try:
            pages = self.dep.obterOrgaosDeputado(assemblyman_id, dataInicio=di, dataFim=df)
            for item in [cm for page in pages for cm in page]:
                end_date = self._parse_datetime(item['dataFim'])
                if (item['dataFim'] is None or end_date > final_date):
                    orgao = Orgao()
                    orgao.nome = item.get("nomeOrgao")
                    orgao.sigla = item.get("siglaOrgao")
                    orgao.cargo = item.get("titulo")
                    commissions.append(orgao)
            return commissions
        except CamaraDeputadosError as error:
            logging.error("[BR1] %s", error)
            return [{'nomeOrgao': None}]

    def get_all_events(self, final_date):
        """
        Gets all events that occurred or were scheduled to this report's period

        :param final_date: Report period final date
        :type final_date: Datetime
        :return: List of events
        :rtype: List[Dict]
        """
        di, df = self.obterDataInicialEFinal(final_date)
        pages = self.ev.obterTodosEventos(
            dataInicio=di,
            dataFim=df
        )
        return [self.build_event(event) for page in pages for event in page]

    def build_event(self, event_info):
        """
        Builds an Event object with given event data

        :param event_info: Event dict
        :type event_info: Dict
        :return: Event object
        :rtype: Evento
        """
        event = Evento()
        event.id = str(event_info['id'])
        event.data_inicial = self._get_brt(
            self._parse_datetime(event_info.get('dataHoraInicio')))
        event.data_final = self._get_brt(
            self._parse_datetime(event_info.get('dataHoraFim')))
        event.situacao = event_info.get('situacao')
        event.nome = event_info.get('descricao')
        event.url = event_info.get('uri')
        event.orgaos = [
            Orgao(nome=o.get('nome'), apelido=o.get('apelido')) for o in event_info.get('orgaos', [])
        ]
        return event

    def get_attended_events(self, events, assemblyman_id):
        """
        Gets all events that assemblyman attended in report's period

        :param events: List of all events of report
        :type events: List[Evento]
        :param assemblyman_id: Assemblyman id
        :type assemblyman_id: String
        :return: List of attended events
        :rtype: List[Evento]
        """
        assemblyman_attented_event = lambda x: [
            am for am in self.ev.obterDeputadosEvento(x['id']) if am['id'] == assemblyman_id]
        return [e for e in events if assemblyman_attented_event(e)]

    def get_expected_events(self, assemblyman_id, final_date):
        """
        Get all events assemblyman was expected to attend

        :param assemblyman_id: Assemblyman id
        :type assemblyman_id: String
        :param final_date: Repor period final date
        :type final_date: Datetime
        :return: List of expected events
        :rtype: List[Dict]
        """
        di, df = self.obterDataInicialEFinal(final_date)
        try:
            pages = self.dep.obterEventosDeputado(
                assemblyman_id,
                dataInicio=di,
                dataFim=df
            )
            return [self.build_event(event) for page in pages for event in page]
        except CamaraDeputadosError as e:
            logging.error("[BR1] {}".format(e))
            return [{'id': None}]

    def get_event_program(self, event_id):
        """
        Gets a event's program, listing all propositions that were discussed

        :param event_id: Event id
        :type event_id: String
        :return: List of propositions discussed
        :rtype: List[Dict]
        """
        try:
            program = self.ev.obterPautaEvento(event_id)
            if not program:
                return []
            propositions = []
            unique_ids = []
            for proposition in program:
                proposition_id = proposition['proposicao_']['id']
                if proposition_id not in unique_ids and proposition_id != None:
                    unique_ids.append(proposition_id)
                    propositions.append(proposition)
                    proposition['proposicao_detalhes'] = self._get_proposition_details(
                        proposition_id)
            return propositions
        except CamaraDeputadosError as error:
            logging.error("[BR1] %s", error)
            return [{'error': True}]

    def _get_proposition_details(self, proposition_id):
        try:
            return self.prop.obterProposicao(proposition_id)
        except CamaraDeputadosError as error:
            logging.warning("[BR1] %s", error)
            return [{'error': True}]

    def get_votes(self, assemblyman_id, proposition, event_dates):
        """
        Gets assemblyman votes on given proposition (and its amendments) of an specific event

        :param assemblyman_id: Assemblyman id
        :type assemblyman_id: String
        :param proposition: Proposition dict
        :type proposition: Dict
        :param event_dates: Start and end date of event
        :type event_dates: Dict
        :return: Assemblyman votes on the proposition
        :rtype: String
        """
        try:
            pautas = []
            votes = []
            for voting in self.prop.obterVotacoesProposicao(
                    tipo=proposition['tipo'],
                    numero=proposition['numero'],
                    ano=proposition['ano']
            ):
                voting_date = datetime.strptime(
                    "{} {}".format(voting["data"], voting["hora"]),
                    "%d/%m/%Y %H:%M"
                )
                if (voting_date >= event_dates['data_inicial'] and
                        voting_date <= event_dates['data_final']):
                    pautas.append(voting['resumo'])
                    votes = [
                        vote['voto'] for vote in voting['votos'] if vote['id'] == assemblyman_id]
            if votes == [] and pautas != []:
                return 'Não votou', ','.join(pautas)
            return ','.join(votes), ','.join(pautas)
        except (CamaraDeputadosError, ValueError) as error:
            logging.debug(error)
            return None, None

    def add_attended_events(self, events_attended):
        """
        Adds given attended events to report

        :param events_attended: List of events attended by assemblyman
        :type events_attended: List[Evento]
        :rtype: None
        """
        for event in events_attended:
            event.set_presente()
            program = self.get_event_program(event.id)
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
        proposition = self.build_proposition(item['proposicao_detalhes'])
        vote, voting_agenda = self.get_votes(
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
    
    def get_absent_events(
            self,
            events,
            attended_events,
            expected_events,
            commissions
    ):
        """
        Gets all events that assemblyman was absent

        :param events: All reports' events
        :type events: List[Evento]
        :param attended_events: All events that assemblyman attended
        :type: attended_events: List[Evento]
        :param expected_events: All events that assemblyman was expected
        :type: expected_events: List[Evento]
        :param commissions: List of assemblyman's commissions
        :type commissions: List[Orgao]
        :return: List of absent events
        :rtype: List[Evento]
        """
        absent_events = [x for x in events if x not in attended_events]
        return self._classify_absent_types(absent_events, expected_events, commissions)

    def _classify_absent_types(self, absent_events, expected_events, commissions):
        expected_events_ids = [x['id'] for x in expected_events]
        commissions_names = [commission['nomeOrgao'] for commission in commissions]
        for event in absent_events:
            if event['id'] in expected_events_ids:
                event.set_ausente_evento_previsto()
            elif (event['orgaos'][0]['nome'] in commissions_names or
                  event['orgaos'][0]['apelido'] == 'PLEN'):
                event.set_ausencia_evento_esperado()
            else:
                event.set_ausencia_evento_nao_esperado()
        return absent_events

    def add_absent_events(self, absent_events):
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

    def get_propositions(self, assemblyman, final_date):
        """
        Gets all assemblyman's proposed propositions on report's timeframe

        :param assemblyman: Assemblyman object
        :type assemblyman: Parlamentar
        :param final_date: Report interval final date
        :type final_date: Datetime
        :return: List of propositions
        :rtype: List[Proposicao]
        """
        di, df = self.obterDataInicialEFinal(final_date)
        try:
            pages = self.prop.obterTodasProposicoes(
                idDeputadoAutor=assemblyman.id,
                dataApresentacaoInicio=di,
                dataApresentacaoFim=df
            )
            for item in [prop for page in pages for prop in page]:
                if (assemblyman.nome.lower() in 
                        [x['nome'].lower() for x in self.prop.obterAutoresProposicao(item['id'])]):
                    details = self.prop.obterProposicao(item['id'])
                    self.relatorio.proposicoes.append(self.build_proposition(details))
        except CamaraDeputadosError as error:
            logging.error("[BR1] %s", error)
            self.relatorio.aviso_dados = 'Não foi possível obter proposições do parlamentar.'

    def build_proposition(self, prop_info):
        """
        Builds a proposition object with given proposition info

        :param prop_info: Proposition information
        :type prop_info: Dict
        :return: Proposition object
        :rtype: Proposicao
        """
        proposition = Proposicao()
        proposition.id = str(prop_info['id'])
        proposition.data_apresentacao = self._get_brt(
            self._parse_datetime(prop_info.get('dataApresentacao')))
        proposition.ementa = prop_info.get('ementa')
        proposition.numero = str(prop_info.get('numero'))
        proposition.tipo = prop_info.get('siglaTipo')
        proposition.url_documento = prop_info.get('urlInteiroTeor')
        proposition.url_autores = prop_info.get('uriAutores')
        proposition.pauta = prop_info.get('ementa')
        return proposition
    
    def _parse_datetime(self, txt):
        if txt is None:
            return txt
        try:
            # One day API returned Epoch instead of documented format
            date = datetime.fromtimestamp(txt/1000)
        except TypeError:
            return self._try_parse_datetime_formats(txt)

    def _try_parse_datetime_formats(self, txt):
        # Formats that have been used at some point of API history
        for str_format in ['%Y-%m-%d', '%Y-%m-%dT%H:%M']:
            try:
                return datetime.strptime(txt, str_format)
            except ValueError:
                continue
        logging.warn("[BR1] Invalid datetime format: %s", txt)
        return None

    def _get_brt(self, date):
        if date is None:
            return None
        return self.brasilia_tz.localize(date)

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
