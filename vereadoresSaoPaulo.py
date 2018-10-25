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
        for item in self.ver.obterPresenca(
                self.obterDataInicial(data_final, weeks=1), data_final):
            if item:
                for v in item['vereadores']:
                    if v['nome'].lower() == vereador['nome'].lower():
                        for s in v['sessoes']:
                            if s['presenca'] == 'Presente':
                                presenca.append(s['nome'])
                        sessao_total += int(item['totalOrd']) + int(item['totalExtra'])
                        presenca_total += int(v['presenteOrd']) + int(v['presenteExtra'])
                print(item['sessoes'])
                for key, value in item['sessoes'].items():
                    if key in presenca:
                        sessoes_presentes.append(
                            {
                                'evento': {'titulo': key, 'orgaos': [{'apelido':str(value)}]}
                            }
                        )
                    else:
                        sessoes.append({'titulo': key, 'orgaos': [{'apelido':str(value)}]})
        
        return render_template(
            'consulta_deputado.html',
            deputado_nome=vereador['nome'],
            deputado_partido=vereador['siglaPartido'],
            deputado_uf=vereador['siglaUf'],
            deputado_img='https://www.99luca11.com/Users/usuario_sem_foto.png',
            data_inicial=self.obterDataInicial(
                data_final, weeks=1).strftime("%d/%m/%Y"),
            data_final=data_final.strftime("%d/%m/%Y"),
            presenca='{0:.2f}%'.format(100*presenca_total/sessao_total),
            presenca_relativa='{0:.2f}%'.format(100*presenca_total/sessao_total),
            eventos=sessoes_presentes,
            todos_eventos=sessoes
        ), 200
        '''
        total_eventos_ausentes=total_eventos_ausentes,
        orgaos=orgaos,
        orgaos_nome=orgaos_nome,
        eventos=eventos_com_deputado,
        eventos_eventos=lista_evento_com_deputado,
        todos_eventos=demais_eventos,
        proposicoes_deputado=proposicoes_deputado,'''


    def obterVereador(self, nome):
        for item in self.ver.obterVereadores():
            if item['nome'].lower() == nome.lower():
                return item