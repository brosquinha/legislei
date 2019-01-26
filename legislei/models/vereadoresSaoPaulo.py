import json
from datetime import datetime

from flask import render_template, request

from legislei.exceptions import ModelError
from legislei.models.parlamentares import ParlamentaresApp
from legislei.models.relatorio import (Evento, Orgao, Parlamentar, Proposicao,
                                       Relatorio)
from legislei.SDKs.CamaraMunicipalSaoPaulo.base import CamaraMunicipal


class VereadoresApp(ParlamentaresApp):

    def __init__(self):
        super().__init__()
        self.ver = CamaraMunicipal()
        self.relatorio = Relatorio()
    
    def obter_relatorio(self, parlamentar_id, data_final=datetime.now(), periodo_dias=7):
        try:
            self.relatorio = Relatorio()
            self.relatorio.set_aviso_dados(u'Apenas dados de pautas de sessões plenárias estão implementados.')
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
                        evento.set_nome(key)
                        proposicao = Proposicao()
                        proposicao.set_pauta(str(value))
                        evento.add_pautas(proposicao)
                        if key in presenca:
                            evento.set_presente()
                            self.relatorio.add_evento_presente(evento)
                        else:
                            evento.set_ausencia_evento_esperado()
                            self.relatorio.add_evento_ausente(evento)
            self.relatorio.set_eventos_ausentes_esperados_total(sessao_total - presenca_total)
            return self.relatorio
        except Exception as e:
            raise e
            # raise ModelError(str(e))


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
