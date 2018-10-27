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
        def tratarDadosTxt(regex, txt, dict_params):
            """
            Obtém um campo de dados do formato arbitrário da CMSP e retorna
            um dicionário muito mais simpático.

            O parâmetro `dict_params` é uma lista de chaves para o dicionário,
            com os elementos posicionados de tal forma a bater com o índice do
            grupo do regex a qual ele se refere. Exemplo:

            ```
            liderancas = tratarDadosTxt(
                r'^([^\^\#]*)\^i([^\^\#]*)\^f([^\^\#]*)(\^c([^\^\#]*))?$',
                liderancas_txt,
                ['partido', 'dataInicio', 'dataFim', '', 'cargo']
            )
            ```
            Args:
                param regex: Regex para capturar os dados do txt
                param txt: String de dados do txt
                param dict_params: Lista de parâmetros para o dict de saída

            Returns:
                Dicionário dos dados de entrada do txt filtrados com o regex
                ordenados de acordo com dicionário de parâmetros
            """
            lista = []
            if txt != '#':
                for item in txt[1:].split('%'):
                    item_re = re.search(regex, item)
                    if item_re == None:
                        continue
                    lista_item = {}
                    i = 1
                    for p in dict_params:
                        if p != '':
                            lista_item[p] = item_re.group(i)
                        i += 1
                    lista.append(lista_item)
            return lista

        vereadores = []
        r = self.http.request(
            'GET',
            'http://www.saopaulo.sp.leg.br/wp-content/uploads/dados_abertos/vereador/vereador.txt'
        )
        dados = r.data.decode('latin_1').replace('\r\n', '\n').encode('utf-8').decode('utf-8')
        buscas = re.finditer(
            r'^(\d{1,5})((\#([^\#]*)){3})(\#(([^\^\#]*)(\^i[^\^\#]*)(\^f[^\^\#]*)(\^c[^\^\#]*)?\%)*)(\#([^\#]*))(\#(((\^p\d)(\^n\d+)(\^s\w+)(\^q[\d\.]+)?)\%)*)(\#((\^i[\d\/]+)(\^f[\d\/]+)(\^s\w+)?(\^p[^\%\#\^]+)?(\^[cbd][^\%\#]+)*\%)*)(\#((\^n[^\^]*)?(\^i[\d\/]*)?(\^f[\d\/]+)?(\^c[^\%\^]+)?(\^d[^\%]+)?\%)*)$',
            dados, re.MULTILINE)
        for busca in buscas:
            registro = busca.group(1) #Não é o ID utilizado pelo resto do sistema
            nomes = busca.group(2).split('#') #Nome, NomeParlamentar, Outros nomes
            if nomes[2]:
                #TODO: Cruzar dados com a outra API da CMSP para obter o nome que ela utiliza
                if '%' in nomes[2]:
                    nome_vereador = nomes[2].split('%')[1]
                else:
                    nome_vereador = nomes[2]
            elif nomes[1]:
                nome_vereador = nomes[1]
            else:
                nome_vereador = nomes[0]
            liderancas = tratarDadosTxt(
                r'^([^\^\#]*)\^i([^\^\#]*)\^f([^\^\#]*)(\^c([^\^\#]*))?$',
                busca.group(5),
                ['partido', 'dataInicio', 'dataFim', '', 'cargo']
            )
            mesa_diretora = busca.group(12) #TODO: Tratar!
            legislaturas = tratarDadosTxt(
                r'^\^p(\d)\^n(\d+)\^s(\w+)(\^q([\d\.]+))?$',
                busca.group(13),
                ['periodo', 'numeroLegislatura', 'situacao', '', 'votos']
            )
            mandatos = tratarDadosTxt(
                r'^\^i([\d\/]+)\^f([\d\/]+)(\^s(\w+))?(\^p([^\%\#\^]+))?(\^[cbd]([^\%\#]+))*$',
                busca.group(20),
                ['dataInicio', 'dataFim', '', 'situacao', '',  'partido', '', 'extras'] #TODO: Tratar extras
            )
            comissoes = tratarDadosTxt(
                r'^(\^n([^\^]*))(\^i([\d\/]*))?(\^f([\d\/]+))?(\^c([^\%\^]+))?(\^d([^\%]+))?$',
                busca.group(27),
                ['', 'nome', '', 'dataIncio', '', 'dataFim', '', 'cargo', '', 'obs']
            )
            if len(mandatos):
                partido = mandatos[-1]['partido']
            else:
                partido = 'NA'
            
            vereadores.append(
                {
                    'registro': registro,
                    'nome': nome_vereador,
                    'siglaPartido': partido,
                    'liderancas': liderancas,
                    'legislaturas': legislaturas,
                    'mesaDiretora': mesa_diretora,
                    'mandatos': mandatos,
                    'comissoes': comissoes
                }
            )
        return vereadores


    def obterAtualLegislatura(self):
        #TODO
        return '17'