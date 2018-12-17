import json
from time import time
from datetime import datetime
from flask import render_template, request
from SDKs.CamaraDeputados.entidades import Deputados, Eventos, Proposicoes, Votacoes
from SDKs.CamaraDeputados.exceptions import CamaraDeputadosError
from models.parlamentares import ParlamentaresApp
from exceptions import ModelError
from models.relatorio import Relatorio, Orgao, Proposicao, Evento


class DeputadosApp(ParlamentaresApp):

    def __init__(self):
        super().__init__()
        self.dep = Deputados()
        self.ev = Eventos()
        self.prop = Proposicoes()
        self.vot = Votacoes()
        self.relatorio = Relatorio()

    def consultar_deputado(self, deputado_id, data_final=None, periodo_dias=7):
        try:
            self.relatorio = Relatorio()
            self.relatorio.set_parlamentar_cargo('deputado federal')
            start_time = time()
            if data_final:
                data_final = datetime.strptime(data_final, '%Y-%m-%d')
                print(data_final)
            else:
                data_final = datetime.now()
            self.setPeriodoDias(periodo_dias)
            deputado_info = self.dep.obterDeputado(deputado_id)
            self.relatorio.set_parlamentar_id(deputado_info['id'])
            self.relatorio.set_parlamentar_nome(deputado_info['ultimoStatus']['nome'])
            self.relatorio.set_parlamentar_partido(deputado_info['ultimoStatus']['siglaPartido'])
            self.relatorio.set_parlamentar_uf(deputado_info['ultimoStatus']['siglaUf'])
            self.relatorio.set_parlamentar_foto(deputado_info['ultimoStatus']['urlFoto'])
            self.relatorio.set_data_inicial(self.obterDataInicial(
                data_final, **self.periodo))
            self.relatorio.set_data_final(data_final)
            print('Deputado obtido em {0:.5f}'.format(time() - start_time))
            (
                eventos,
                presenca_total,
                todos_eventos
            ) = self.procurarEventosComDeputado(
                deputado_info['id'],
                data_final
            )
            print('Eventos obtidos em {0:.5f}'.format(time() - start_time))
            orgaos = self.obterOrgaosDeputado(deputado_info['id'], data_final)
            print('Orgaos obtidos em {0:.5f}'.format(time() - start_time))
            orgaos_nomes = [orgao['nomeOrgao'] for orgao in orgaos]
            for e in eventos:
                evento = Evento()
                evento.set_data_inicial(e['dataHoraInicio'])
                evento.set_data_final(e['dataHoraFim'])
                evento.set_situacao(e['descricaoSituacao'])
                evento.set_nome(e['titulo'])
                evento.set_presente()
                evento.set_url(e['uri'])
                for o in e['orgaos']:
                    orgao = Orgao()
                    orgao.set_nome(o['nome'])
                    orgao.set_apelido(o['apelido'])
                    evento.add_orgaos(orgao)
                pautas = self.obterPautaEvento(e['id'])
                if pautas == [{'error': True}]:
                    evento.add_pautas(None)
                else:
                    for pauta in pautas:
                        if len(pauta['votacao']):
                            proposicao = Proposicao()
                            if pauta['proposicao_detalhes'] == [{'error': True}]:
                                proposicao = None
                            else:
                                proposicao.set_tipo(pauta['proposicao_detalhes']['siglaTipo'])
                                proposicao.set_url_documento(
                                    pauta['proposicao_detalhes']['urlInteiroTeor'])
                                proposicao.set_url_autores(
                                    pauta['proposicao_detalhes']['uriAutores'])
                            if pauta['votacao'] == [{'error': True}]:
                                proposicao.set_voto('ERROR')
                            else:
                                voto = self.obterVotoDeputado(
                                    pauta['votacao'][0]['id'], deputado_info['id'])
                                proposicao.set_pauta(pauta['proposicao_detalhes']['ementa'])
                                proposicao.set_voto(voto)
                            evento.add_pautas(proposicao)
                self.relatorio.add_evento_presente(evento)
            print('Pautas obtidas em {0:.5f}'.format(time() - start_time))
            (
                eventos_ausentes,
                eventos_ausentes_total,
                eventos_previstos
            ) = self.obterEventosAusentes(
                deputado_info['id'],
                data_final,
                eventos,
                orgaos_nomes,
                todos_eventos
            )
            self.relatorio.set_eventos_ausentes_esperados_total(eventos_ausentes_total)
            for e in eventos_ausentes:
                evento = Evento()
                if e['controleAusencia'] == 1:
                    evento.set_ausente_evento_previsto()
                elif e['controleAusencia'] == 2:
                    evento.set_ausencia_evento_esperado()
                else:
                    evento.set_ausencia_evento_nao_esperado()
                evento.set_data_inicial(e['dataHoraInicio'])
                evento.set_data_final(e['dataHoraFim'])
                evento.set_nome(e['titulo'])
                evento.set_situacao(e['descricaoSituacao'])
                evento.set_url(e['uri'])
                for o in e['orgaos']:
                    orgao = Orgao()
                    orgao.set_nome(o['nome'])
                    orgao.set_apelido(o['apelido'])
                    evento.add_orgaos(orgao)
                self.relatorio.add_evento_ausente(evento)
                if evento.get_presenca() > 1:
                    self.relatorio.add_evento_previsto(evento)
            print('Ausencias obtidas em {0:.5f}'.format(time() - start_time))
            self.obterProposicoesDeputado(deputado_info, data_final)
            print('Proposicoes obtidas em {0:.5f}'.format(time() - start_time))
            
            return self.relatorio
        except CamaraDeputadosError:
            raise ModelError("API Câmara dos Deputados indisponível")

    def obterOrgaosDeputado(self, deputado_id, data_final=datetime.now()):
        orgaos = []
        di = self.formatarDatasYMD(
            self.obterDataInicial(data_final, **self.periodo)
        )
        try:
            for page in self.dep.obterOrgaosDeputado(deputado_id, dataInicial=di):
                for item in page:
                    dataFim = datetime.now()
                    if item['dataFim'] != None:
                        try:
                            # Um belo dia a API retornou Epoch ao invés do formato documentado (YYYY-MM-DD), então...
                            dataFim = datetime.fromtimestamp(item['dataFim']/1000)
                        except TypeError:
                            dataFim = datetime.strptime(item['dataFim'], '%Y-%m-%d')
                    if (item['dataFim'] == None or dataFim > data_final):
                        orgao = Orgao()
                        if 'nomeOrgao' in item:
                            orgao.set_nome(item['nomeOrgao'])
                        if 'siglaOrgao' in item:
                            orgao.set_sigla(item['siglaOrgao'])
                        if 'nomePapel' in item:
                            orgao.set_cargo(item['nomePapel'])
                        self.relatorio.add_orgao(orgao)
                        orgaos.append(item)
            return orgaos
        except CamaraDeputadosError:
            return [{'nomeOrgao': None}]

    def procurarEventosComDeputado(self, deputado_id, data_final=datetime.now()):
        eventos_com_deputado = []
        eventos_totais = []
        di, df = self.obterDataInicialEFinal(data_final)
        for page in self.ev.obterTodosEventos(
            dataInicio=di,
            dataFim=df
        ):
            for item in page:
                eventos_totais.append(item)
                for dep in self.ev.obterDeputadosEvento(item['id']):
                    if dep['id'] == deputado_id:
                        eventos_com_deputado.append(item)
        if len(eventos_totais) == 0:
            presenca = 0
        else:
            presenca = 100*len(eventos_com_deputado)/len(eventos_totais)
        return eventos_com_deputado, presenca, eventos_totais

    def obterEventosPrevistosDeputado(self, deputado_id, data_final):
        di, df = self.obterDataInicialEFinal(data_final)
        eventos = []
        try:
            for page in self.dep.obterEventosDeputado(
                deputado_id,
                dataInicio=di,
                dataFim=df
            ):
                for item in page:
                    eventos.append(item)
            return eventos
        except CamaraDeputadosError:
            eventos = [{'id': None}]

    def obterPautaEvento(self, ev_id):
        try:
            pautas = self.ev.obterPautaEvento(ev_id)
            if not pautas:
                return []
            pautas_unicas = []
            pautas_unicas_ids = []
            for p in pautas:
                proposicao_id = p['proposicao_']['id']
                if proposicao_id not in pautas_unicas_ids and proposicao_id != None:
                    pautas_unicas_ids.append(proposicao_id)
                    pautas_unicas.append(p)
                    try:
                        p['proposicao_detalhes'] = self.prop.obterProposicao(
                            proposicao_id)
                    except CamaraDeputadosError:
                        p['proposicao_detalhes'] = [{'error': True}]
                    try:
                        p['votacao'] = self.prop.obterVotacoesProposicao(
                            proposicao_id)
                    except CamaraDeputadosError:
                        p['votacao'] = [{'error': True}]
            return pautas_unicas
        except CamaraDeputadosError:
            return [{'error': True}]

    def obterVotoDeputado(self, vot_id, dep_id):
        try:
            for page in self.vot.obterVotos(vot_id):
                for v in page:
                    if v['parlamentar']['id'] == dep_id:
                        return v['voto']
        except CamaraDeputadosError:
            return False

    def obterEventosAusentes(
            self,
            dep_id,
            data_final,
            eventos_dep,
            orgaos_dep,
            todos_eventos
    ):
        demais_eventos = [x for x in todos_eventos if x not in eventos_dep]
        eventos_previstos = self.obterEventosPrevistosDeputado(
            dep_id, data_final)
        if eventos_previstos:
            eventos_previstos = [x['id'] for x in eventos_previstos]
        else:
            eventos_previstos = []
        ausencia = 0
        for e in demais_eventos:
            if (e['id'] in eventos_previstos):
                ausencia += 1
                e['controleAusencia'] = 1
            elif (e['orgaos'][0]['nome'] in orgaos_dep or
                    e['orgaos'][0]['apelido'] == 'PLEN'):
                ausencia += 1
                e['controleAusencia'] = 2
            else:
                e['controleAusencia'] = None
        return demais_eventos, ausencia, eventos_previstos

    def obterProposicoesDeputado(self, deputado, data_final):
        di, df = self.obterDataInicialEFinal(data_final)
        try:
            for page in self.prop.obterTodasProposicoes(
                idAutor=deputado['id'],
                dataApresentacaoInicio=di,
                dataApresentacaoFim=df
            ):
                for item in page:
                    if (deputado['ultimoStatus']['nome'].lower() in 
                            [x['nome'].lower() for x in self.prop.obterAutoresProposicao(item['id'])]):
                        proposicao = Proposicao()
                        p = self.prop.obterProposicao(item['id'])
                        if 'dataApresentacao' in p:
                            proposicao.set_data_apresentacao(p['dataApresentacao'])
                        if 'ementa' in p:
                            proposicao.set_ementa(p['ementa'])
                        if 'numero' in p:
                            proposicao.set_numero(p['numero'])
                        if 'siglaTipo' in p:
                            proposicao.set_tipo(p['siglaTipo'])
                        if 'urlInteiroTeor' in p:
                            proposicao.set_url_documento(p['urlInteiroTeor'])
                        self.relatorio.add_proposicao(proposicao)
        except CamaraDeputadosError:
            #TODO
            pass

    def obterTramitacoesDeputado(self, dep_id, data_final):
        di, df = self.obterDataInicialEFinal(data_final)
        props = []
        for page in self.prop.obterTodasProposicoes(
            idAutor=dep_id,
            dataInicio=di,
            dataFim=df
        ):
            for item in page:
                props.append(item)
        return props

    def obterDeputados(self):
        deputados = []
        for page in self.dep.obterTodosDeputados():
            for item in page:
                deputados.append(item)
        return json.dumps(deputados), 200
