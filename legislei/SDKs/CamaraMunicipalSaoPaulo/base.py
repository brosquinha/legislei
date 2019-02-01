import certifi
import urllib3
import xml.etree.ElementTree as ET
import json
import re
from datetime import timedelta, datetime

class CamaraMunicipal(object):
    """ Base class
    """

    def __init__(self):
        self.http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where()
        )

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
                    elif child.tag == 'Presencas':
                        presenca['totalOrd'] = child.attrib['TotalSessoesOrdinarias']
                        presenca['totalExtra'] = child.attrib['TotalSessoesExtraOrdinarias']
                sessoes_nomes = set(sessoes_nomes)
                for sessao in sessoes_nomes:
                    # presenca['sessoes'][sessao] = self.obterPautaSessao(
                    #     data_controle, sessao)
                    presenca['sessoes'][sessao] = self.obterVotacoesSessao(
                        data_controle, sessao
                    )
            data_controle = data_controle + timedelta(days=1)
            presenca_total.append(presenca)
        return presenca_total

    def obterVotacoesSessao(self, data, nome):
        votacoes = []
        data_sessao = None
        r = self.http.request(
            'GET',
            'https://splegispdarmazenamento.blob.core.windows.net/containersip/VOTACOES_{:02d}_{:02d}_{}.xml'.format(
                data.day, data.month, data.year
            )
        )
        if r.status != 200:
            print("Sem votacoes nesse dia")
        else:
            root = ET.fromstring(r.data.decode('utf-8'))
            for child in root:
                if child.tag == 'Sessao':
                    if child.attrib['Nome'] == nome:
                        data_sessao = child.attrib['Data']
                        for v in child:
                            votacao = {
                                'pauta': v.attrib['Materia'],
                                'projeto': v.attrib['Ementa'],
                                'votos': []
                            }
                            for voto in v:
                                if voto.tag == 'Vereador':
                                    votacao['votos'].append({
                                        'id': voto.attrib['IDParlamentar'],
                                        'nome': voto.attrib['Nome'],
                                        'voto': voto.attrib['Voto']
                                    })
                            votacoes.append(votacao)
        return {'pautas': votacoes, 'data': data_sessao}

    def obterPautaSessao(self, data, nome):
        projetos = {
            'pautas': [],
            'situacao': None,
            'id': None
        }
        r = self.http.request(
            'POST',
            'http://splegisws.camara.sp.gov.br/ws/ws2.asmx/PautasSessoesPlenariasJSON',
            encode_multipart=False,
            fields={'Ano': data.year},
        )
        for item in json.loads(r.data.decode('utf-8')):
            if nome in item['sessao']:
                projetos = {
                    'pautas': self.obterPautaEstendidaSessao(item['chave']),
                    'situacao': item['status'],
                    'id': item['chave']
                }
        return projetos

    def obterPautaEstendidaSessao(self, sessao_id):
        ementas = []
        r = self.http.request(
            'POST',
            'http://splegisws.camara.sp.gov.br/ws/ws2.asmx/PautaEstendidaSessaoPlenariaJSON',
            encode_multipart=False,
            fields={'Chave': sessao_id},
        )
        for item in json.loads(r.data.decode('utf-8'))['projetos']:
            ementas.append({
                'ementa': item['ementa'],
                'tipo': item['tipo'], 
                'numero': item['numero']
            })
        return ementas

    def obterProjetosParlamentar(self, parlamentar_nome, ano, tipo='PL'):
        projetos = []
        r = self.http.request(
            'POST',
            'http://splegisws.camara.sp.gov.br/ws/ws2.asmx/ProjetosAutoresJSON',
            encode_multipart=False,
            fields={'ano': ano, 'tipo': tipo, 'numero': ''},
        )
        for item in json.loads(r.data.decode('utf-8')):
            if 'leitura' in item and 'autores' in item:
                try:
                    for autor in item['autores']:
                        if autor['nome'].lower() == parlamentar_nome.lower():
                            timestamp_str = re.match(r'\/Date\((\d*)\)', item['leitura'])
                            projetos.append({
                                'tipo': item['tipo'],
                                'numero': item['numero'],
                                'ano': item['ano'],
                                'data': datetime.fromtimestamp(int(timestamp_str.group(1))/1000)
                            })
                except Exception:
                    #TODO
                    pass
        return projetos

    def obterProjetosDetalhes(self, ano):
        r = self.http.request(
            'POST',
            'http://splegisws.camara.sp.gov.br/ws/ws2.asmx/ProjetosPorAnoJSON',
            encode_multipart=False,
            fields={'ano': ano},
        )
        return json.loads(r.data.decode('utf-8'))

    def obterOcupacaoGabinete(self):
        r = self.http.request(
            'POST',
            'http://splegisws.camara.sp.gov.br/ws/ws2.asmx/OcupacaoGabineteJSON',
            encode_multipart=False
        )
        if r.status != 200:
            raise Exception('API call failed')
        try:
            data_json = json.loads(r.data.decode('utf-8'))
            return self.converterDataEmTime(data_json, ['inicio', 'fim'])
        except:
            raise Exception('Failed to decode API data')

    def converterDataEmTime(self, json, params_para_converter):
        for item in json:
            for key, value in item.items():
                if key in params_para_converter:
                    value_re = re.match(r'^\/Date\((\d+)\)\/$', value)
                    if value_re == None:
                        continue
                    item[key] = datetime.utcfromtimestamp(int(value_re.group(1))/1000)
        return json

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
        gabinetes = self.obterOcupacaoGabinete()
        buscas = re.finditer(
            r'^(\d{1,5})((\#([^\#]*)){3})(\#(([^\^\#]*)(\^i[^\^\#]*)(\^f[^\^\#]*)(\^c[^\^\#]*)?\%)*)(\#([^\#]*))(\#(((\^p\d)(\^n\d+)(\^s\w+)(\^q[\d\.]+)?)\%)*)(\#((\^i[\d\/]+)(\^f[\d\/]+)(\^s\w+)?(\^p[^\%\#\^]+)?(\^[cbd][^\%\#]+)*\%)*)(\#((\^n[^\^]*)?(\^i[\d\/]*)?(\^f[\d\/]+)?(\^c[^\%\^]+)?(\^d[^\%]+)?\%)*)$',
            dados, re.MULTILINE)
        for busca in buscas:
            registro = busca.group(1) #Não é o ID utilizado pelo resto do sistema
            tipos_nomes = busca.group(2).split('#') #Nome, NomeParlamentar, Outros nomes
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
            vereador_id = None
            if len(legislaturas):
                gabinetes_nomes = [x['vereador'].lower() for x in gabinetes]
                nome_vereador = None
                for tipo in tipos_nomes:
                    for nome in tipo.split('%'):
                        if nome.lower() in gabinetes_nomes:
                            nome_vereador = nome
                            vereador_id = 'TODO'
                            for gabinete in gabinetes:
                                if gabinete['vereador'].lower() == nome.lower():
                                    vereador_id = gabinete['codigo']
                if nome_vereador == None:
                    nome_vereador = 'ERRO1'.join(tipos_nomes)
            else:
                nome_vereador = 'ERRO2'
            
            vereadores.append(
                {
                    'registro': registro,
                    'id': vereador_id,
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