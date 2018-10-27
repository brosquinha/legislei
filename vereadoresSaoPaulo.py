import json
from datetime import datetime
from flask import render_template, request
from SDKs.CamaraMunicipalSaoPaulo.base import CamaraMunicipal
from parlamentares import ParlamentaresApp

class VereadoresApp(ParlamentaresApp):

    def __init__(self):
        self.ver = CamaraMunicipal()
    
    def consultar_vereador(self):
        data_final = datetime.strptime(request.form['data'], '%Y-%m-%d')
        print(request.form['deputado'])
        vereador = self.obterVereador(request.form['deputado'])
        presenca = []
        sessoes_presentes = []
        sessao_total = 0
        presenca_total = 0
        sessoes = []
        for dia in self.ver.obterPresenca(
                self.obterDataInicial(data_final, weeks=1), data_final):
            if dia:
                for v in dia['vereadores']:
                    if v['nome'].lower() == vereador['nome'].lower():
                        for s in v['sessoes']:
                            if s['presenca'] == 'Presente':
                                presenca.append(s['nome'])
                        sessao_total += int(dia['totalOrd']) + int(dia['totalExtra'])
                        presenca_total += int(v['presenteOrd']) + int(v['presenteExtra'])
                #print(item['sessoes'])
                for key, value in dia['sessoes'].items():
                    if key in presenca:
                        sessoes_presentes.append(
                            {
                                'titulo': key,
                                'pauta': str(value)
                            }
                        )
                    else:
                        sessoes.append(
                            {
                                'titulo': key,
                                'pauta': str(value)
                            }
                        )
        
        return render_template(
            'consulta_vereador.html',
            politico_nome=vereador['nome'],
            politico_partido=vereador['siglaPartido'],
            politico_uf='São Paulo',
            politico_img='https://www.99luca11.com/Users/usuario_sem_foto.png',
            data_inicial=self.obterDataInicial(
                data_final, weeks=1).strftime("%d/%m/%Y"),
            data_final=data_final.strftime("%d/%m/%Y"),
            presenca='{0:.2f}%'.format(100*presenca_total/sessao_total),
            presenca_relativa='{0:.2f}%'.format(100*presenca_total/sessao_total),
            eventos_presentes=sessoes_presentes,
            eventos_ausentes=sessoes
        ), 200


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