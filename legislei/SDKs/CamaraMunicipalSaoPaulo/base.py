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
                            'chave': child.attrib['IDParlamentar'],
                            'presenteOrd': child.attrib['PresenteOrd'],
                            'presenteExtra': child.attrib['PresenteExtra'],
                            'sessoes': child_sessoes
                        })
                    elif child.tag == 'Presencas':
                        presenca['totalOrd'] = child.attrib['TotalSessoesOrdinarias']
                        presenca['totalExtra'] = child.attrib['TotalSessoesExtraOrdinarias']
                sessoes_nomes = set(sessoes_nomes)
                for sessao in sessoes_nomes:
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
                                        'chave': voto.attrib['IDParlamentar'],
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

    def obterProjetosParlamentar(self, parlamentar_id, ano, tipo='PL'):
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
                        if str(autor['chave']) == parlamentar_id.lower():
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
        r = self.http.request(
            'POST',
            'http://splegisws.camara.sp.gov.br/ws/ws2.asmx/VereadoresCMSPJSON',
            encode_multipart=False
        )
        if r.status != 200:
            raise Exception('API call failed')
        try:
            data_json = json.loads(r.data.decode('utf-8'))
            vereadores = []
            for vereador in data_json:
                self.converterDataEmTime(vereador['mandatos'], ['inicio', 'fim'])
                legislatura_atual = False
                for mandato in vereador['mandatos']:
                    if mandato['fim'] > datetime.now():
                        legislatura_atual = True
                if not legislatura_atual:
                    continue
                self.converterDataEmTime(vereador['cargos'], ['inicio', 'fim'])
                self.converterDataEmTime(vereador['filiacoes'], ['inicio', 'fim'])
                vereadores.append(vereador)
            return vereadores
        except:
            raise Exception('Failed to decode API data')
