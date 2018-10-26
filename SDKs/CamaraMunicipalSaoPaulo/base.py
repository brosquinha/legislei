import urllib3
import xml.etree.ElementTree as ET
import json
import re
from datetime import timedelta, datetime

class CamaraMunicipal(object):
    """ Base class
    """

    def __init__(self):
        self.http = urllib3.PoolManager()

    def obterPresenca(self, data_inicio, data_fim):
        data_controle = data_inicio
        presenca_total = []
        while data_controle <= data_fim:
            r = self.http.request(
                'GET',
                'https://splegispdarmazenamento.blob.core.windows.net/containersip/PRESENCAS_{:02d}_{:02d}_{}.xml'.format(
                    data_controle.day, data_controle.month, data_controle.year
                )
            )
            if r.status != 200:
                print("Sem relatorio nesse dia")
                presenca = None
            else:
                presenca = {'vereadores': [], 'sessoes': {}}
                sessoes_nomes = []
                root = ET.fromstring(r.data.decode('utf-8'))
                for child in root:
                    child_sessoes = []
                    if child.tag == 'Vereador':
                        for sessao in child:
                            if sessao.tag == 'Sessao':
                                sessoes_nomes.append(sessao.attrib['Nome'])
                                child_sessoes.append({
                                    'nome': sessao.attrib['Nome'],
                                    'presenca': sessao.attrib['Presenca'],
                                })
                        presenca['vereadores'].append({
                            'nome': child.attrib['Nome'],
                            'presenteOrd': child.attrib['PresenteOrd'],
                            'presenteExtra': child.attrib['PresenteExtra'],
                            'sessoes': child_sessoes
                        })
                        '''print('{}: {} + {} presencas'.format(
                            child.attrib['Nome'],
                            child.attrib['PresenteOrd'],
                            child.attrib['PresenteExtra']
                        ))'''
                    elif child.tag == 'Presencas':
                        presenca['totalOrd'] = child.attrib['TotalSessoesOrdinarias']
                        presenca['totalExtra'] = child.attrib['TotalSessoesExtraOrdinarias']
                        '''print('Total: {} + {}'.format(
                            child.attrib['TotalSessoesOrdinarias'],
                            child.attrib['TotalSessoesExtraOrdinarias']
                        ))'''
                sessoes_nomes = set(sessoes_nomes)
                for sessao in sessoes_nomes:
                    presenca['sessoes'][sessao] = self.obterPautaSessao(
                        data_controle, sessao)
            data_controle = data_controle + timedelta(days=1)
            presenca_total.append(presenca)
        return presenca_total

    def obterPautaSessao(self, data, nome):
        projetos = []
        r = self.http.request(
            'POST',
            'http://splegisws.camara.sp.gov.br/ws/ws2.asmx/PautasSessoesPlenariasJSON',
            encode_multipart=False,
            fields={'Ano': data.year},
        )
        for item in json.loads(r.data.decode('utf-8')):
            if nome in item['sessao']:
                print(item['sessao'])
                projetos.append(['{}{}'.format(x['tipo'], x['numero']) for x in item['projetos']])
        return projetos

    def obterVereadores(self):
        vereadores = []
        r = self.http.request(
            'GET',
            'http://www.saopaulo.sp.leg.br/wp-content/uploads/dados_abertos/vereador/vereador.txt'
        )
        dados = r.data.decode('latin_1').encode('utf-8').decode('utf-8')
        for item in dados.split('\n'):
            busca = re.search(r'^(\d{3,5})\#(([^\#]+)\#){2}[^\#]*\#([^\#\^]*)\^', item)
            """ TODO: Novo Regex para pegar todas as informações disponíveis
            deste arquivo, incluindo de quais comissões o vereador faz parte.
            Falta capturar mais grupos de dados e aumentar a cobertura (pega
            1535 de 1744)
            ^(\d{3,5})(\#([^\#]*)){3}(\#(([^\^\#]*\^i[^\^\#]*)(\^f[^\^\#]*)(\^c[^\^\#]*)\%)*)(\#([^\#]*))(\#((\^p\d\^n\d+\^s\w+\^q\d+)\%)*)(\#(\^i[\d\/]+\^f[\d\/]+(\^s\w+)?(\^p[\w ]+)?(\^[cbd][^\%\#]+)*\%)*)(\#((\^n[^\^]*)?(\^i[\d\/]*)?(\^f[\d\/]+)?(\^c[^\%]+)?(\^d[^\%]+)?\%)*)$
            """
            if busca:
                if '%' in busca.group(3):
                    nome = busca.group(3).split('%')[1]
                else:
                    nome = busca.group(3)
                vereadores.append(
                    {
                        'id': nome,
                        'nome': nome,
                        'siglaPartido': busca.group(4),
                        'siglaUf': 'SP'
                    }
                )
        return vereadores
