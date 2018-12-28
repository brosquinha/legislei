import json
from datetime import datetime
from flask import render_template, request
from SDKs.CamaraMunicipalSaoPaulo.base import CamaraMunicipal
from models.parlamentares import ParlamentaresApp
from exceptions import ModelError
from models.relatorio import Relatorio, Proposicao, Evento, Orgao

class VereadoresApp(ParlamentaresApp):

    def __init__(self):
        super().__init__()
        self.ver = CamaraMunicipal()
        self.relatorio = Relatorio()
    
    def consultar_vereador(self, vereador_nome, data_final=datetime.now(), periodo=7):
        try:
            self.relatorio = Relatorio()
            self.relatorio.set_aviso_dados(u'Apenas dados de pautas de sessões plenárias estão implementados.')
            self.setPeriodoDias(periodo)
            data_final = datetime.strptime(data_final, '%Y-%m-%d')
            data_inicial = self.obterDataInicial(data_final, **self.periodo)
            vereador = self.obterVereador(vereador_nome)
            self.relatorio.set_parlamentar_cargo('São Paulo')
            self.relatorio.set_parlamentar_nome(vereador['nome'])
            self.relatorio.set_parlamentar_id(vereador['nome']) #Por ora
            self.relatorio.set_parlamentar_partido(vereador['siglaPartido'])
            self.relatorio.set_parlamentar_uf('SP')
            self.relatorio.set_parlamentar_foto(
                'https://www.99luca11.com/Users/usuario_sem_foto.png')
            self.relatorio.set_data_inicial(data_inicial)
            self.relatorio.set_data_final(data_final)
            presenca = []
            sessao_total = 0
            presenca_total = 0
            for dia in self.ver.obterPresenca(data_inicial, data_final):
                if dia:
                    for v in dia['vereadores']:
                        if v['nome'].lower() == vereador['nome'].lower():
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


    def obterVereador(self, nome):
        for item in self.ver.obterVereadores():
            if item['nome'].lower() == nome.lower():
                return item


    def obterVereadoresAtuais(self):
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
        return json.dumps(lista), 200