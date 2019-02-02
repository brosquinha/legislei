import json
from uuid import uuid4
from datetime import datetime

from flask import render_template, request

from legislei.exceptions import ModelError
from legislei.houses.casa_legislativa import CasaLegislativa
from legislei.models.relatorio import (Evento, Orgao, Parlamentar, Proposicao,
                                       Relatorio)
from legislei.SDKs.CamaraMunicipalSaoPaulo.base import CamaraMunicipal


class CamaraMunicipalSaoPauloHandler(CasaLegislativa):

    def __init__(self):
        super().__init__()
        self.ver = CamaraMunicipal()
        self.relatorio = Relatorio()
    
    def obter_relatorio(self, parlamentar_id, data_final=datetime.now(), periodo_dias=7):
        try:
            self.relatorio = Relatorio()
            self.relatorio.set_aviso_dados(u'Dados de sessões de comissões não disponível.')
            self.setPeriodoDias(periodo_dias)
            data_final = datetime.strptime(data_final, '%Y-%m-%d')
            data_inicial = self.obterDataInicial(data_final, **self.periodo)
            vereador = self.obter_parlamentar(parlamentar_id)
            self.relatorio.set_data_inicial(data_inicial)
            self.relatorio.set_data_final(data_final)
            presenca = []
            sessao_total = 0
            presenca_total = 0
            for dia in self.ver.obterPresenca(data_inicial, data_final):
                if dia:
                    for v in dia['vereadores']:
                        if v['nome'].lower() == vereador.get_nome().lower():
                            for s in v['sessoes']:
                                if s['presenca'] == 'Presente':
                                    presenca.append(s['nome'])
                            sessao_total += int(dia['totalOrd']) + int(dia['totalExtra'])
                            presenca_total += int(v['presenteOrd']) + int(v['presenteExtra'])
                    for key, value in dia['sessoes'].items():
                        evento = Evento()
                        orgao = Orgao()
                        orgao.set_nome('Plenário')
                        orgao.set_apelido('PLENÁRIO')
                        evento.add_orgaos(orgao)
                        evento.set_nome(key)
                        evento.set_id(str(uuid4()))
                        if value['data']:
                            evento.set_data_inicial(value['data'])
                            evento.set_data_final(value['data'])
                        for prop in value['pautas']:
                            proposicao = Proposicao()
                            proposicao.set_pauta(prop['projeto'])
                            proposicao.set_tipo(prop['pauta'])
                            for v in prop['votos']:
                                if v['nome'] == parlamentar_id.upper():
                                    proposicao.set_voto(v['voto'])
                            evento.add_pautas(proposicao)
                        if key in presenca:
                            evento.set_presente()
                            self.relatorio.add_evento_presente(evento)
                        else:
                            evento.set_ausencia_evento_esperado()
                            self.relatorio.add_evento_ausente(evento)
            self.relatorio.set_eventos_ausentes_esperados_total(sessao_total - presenca_total)
            self.obter_proposicoes_parlamentar(vereador.get_nome(), data_inicial, data_final)
            return self.relatorio
        except Exception as e:
            print(e)
            raise e
            # raise ModelError(str(e))

    def obter_proposicoes_parlamentar(self, parlamentar_nome, data_inicial, data_final):
        projetos = self.ver.obterProjetosParlamentar(parlamentar_nome, data_final.year)
        projetos_ids = ['{}{}{}'.format(x['tipo'], x['numero'], x['ano']) for x in projetos]
        for projeto in self.ver.obterProjetosDetalhes(data_final.year):
            try:
                if '{}{}{}'.format(projeto['tipo'], projeto['numero'], projeto['ano']) in projetos_ids:
                    projeto_data = datetime.strptime(projeto['data'], '%Y-%m-%dT%H:%M:%S')
                    print(projeto_data)
                    if not(projeto_data >= data_inicial and projeto_data <= data_final):
                        continue
                    proposicao = Proposicao()
                    proposicao.set_data_apresentacao(projeto_data)
                    proposicao.set_ementa(projeto['ementa'])
                    proposicao.set_id(projeto['chave'])
                    proposicao.set_tipo(projeto['tipo'])
                    proposicao.set_numero('{}{}'.format(projeto['numero'], projeto['ano']))
                    proposicao.set_url_documento(
                        'http://documentacao.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=proje&form=A&nextAction=search&indexSearch=^nTw^lTodos%20os%20campos&exprSearch=P={tipo}{numero}{ano}'.format(
                            tipo=projeto['tipo'],
                            numero=projeto['numero'],
                            ano=projeto['ano']
                        )
                    )
                    proposicao.set_url_autores(proposicao.get_url_documento())
                    self.relatorio.add_proposicao(proposicao)
            except Exception as e:
                #TODO
                print(e)

    def obter_parlamentar(self, parlamentar_id):
        for item in self.ver.obterVereadores():
            if item['nome'].lower() == parlamentar_id.lower():
                parlamentar = Parlamentar()
                parlamentar.set_cargo('São Paulo')
                parlamentar.set_nome(item['nome'])
                parlamentar.set_id(item['nome']) #Por ora
                parlamentar.set_partido(item['siglaPartido'])
                parlamentar.set_uf('SP')
                parlamentar.set_foto(
                    'https://www.99luca11.com/Users/usuario_sem_foto.png')
                self.relatorio.set_parlamentar(parlamentar)
                return parlamentar

    def obter_parlamentares(self):
        vereadores = self.ver.obterVereadores()
        atual = self.ver.obterAtualLegislatura()
        lista = []
        for v in vereadores:
            if (len(v['legislaturas']) and 
                    v['legislaturas'][-1]['numeroLegislatura'] == atual):
                lista.append(
                    {
                        'nome': v['nome'],
                        'id': v['nome'],
                        'siglaPartido': v['siglaPartido']
                    }
                )
        return lista
