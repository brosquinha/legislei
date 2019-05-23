import json
from uuid import uuid4
from datetime import datetime

import pytz
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
        self.brasilia_tz = pytz.timezone('America/Sao_Paulo')
    
    def obter_relatorio(self, parlamentar_id, data_final=datetime.now(), periodo_dias=7):
        try:
            self.relatorio = Relatorio()
            self.relatorio.aviso_dados = u'Dados de sessões de comissões não disponível.'
            self.setPeriodoDias(periodo_dias)
            data_final = datetime.strptime(data_final, '%Y-%m-%d')
            data_inicial = self.obterDataInicial(data_final, **self.periodo)
            vereador = self.obter_parlamentar(parlamentar_id)
            self.relatorio.data_inicial = self.brasilia_tz.localize(data_inicial)
            self.relatorio.data_final = self.brasilia_tz.localize(data_final)
            presenca = []
            sessao_total = 0
            presenca_total = 0
            for dia in self.ver.obterPresenca(data_inicial, data_final):
                if dia:
                    for v in dia['vereadores']:
                        if str(v['chave']) == vereador.id:
                            for s in v['sessoes']:
                                if s['presenca'] == 'Presente':
                                    presenca.append(s['nome'])
                            sessao_total += int(dia['totalOrd']) + int(dia['totalExtra'])
                            presenca_total += int(v['presenteOrd']) + int(v['presenteExtra'])
                    for key, value in dia['sessoes'].items():
                        evento = Evento()
                        orgao = Orgao()
                        orgao.nome = 'Plenário'
                        orgao.apelido = 'PLENÁRIO'
                        evento.orgaos.append(orgao)
                        evento.nome = key
                        evento.id = str(uuid4())
                        if value['data']:
                            try:
                                evento.data_inicial = self.brasilia_tz.localize(
                                    datetime.strptime(value['data'], "%d/%m/%Y"))
                                evento.data_final = self.brasilia_tz.localize(
                                    datetime.strptime(value['data'], "%d/%m/%Y"))
                            except ValueError:
                                pass
                        for prop in value['pautas']:
                            proposicao = Proposicao()
                            proposicao.pauta = prop['projeto']
                            proposicao.tipo = prop['pauta']
                            for v in prop['votos']:
                                if str(v['chave']) == parlamentar_id:
                                    proposicao.voto = v['voto']
                            evento.pautas.append(proposicao)
                        if key in presenca:
                            evento.set_presente()
                            self.relatorio.eventos_presentes.append(evento)
                        else:
                            evento.set_ausencia_evento_esperado()
                            self.relatorio.eventos_ausentes.append(evento)
            self.relatorio.eventos_ausentes_esperados_total = sessao_total - presenca_total
            self.obter_proposicoes_parlamentar(vereador.id, data_inicial, data_final)
            return self.relatorio
        except Exception as e:
            print(e)
            #raise e
            raise ModelError(str(e))

    def obter_proposicoes_parlamentar(self, parlamentar_id, data_inicial, data_final):
        projetos = self.ver.obterProjetosParlamentar(parlamentar_id, data_final.year)
        projetos_ids = ['{}{}{}'.format(x['tipo'], x['numero'], x['ano']) for x in projetos]
        for projeto in self.ver.obterProjetosDetalhes(data_final.year):
            try:
                if '{}{}{}'.format(projeto['tipo'], projeto['numero'], projeto['ano']) in projetos_ids:
                    projeto_data = datetime.strptime(projeto['data'], '%Y-%m-%dT%H:%M:%S')
                    print(projeto_data)
                    if not(projeto_data >= data_inicial and projeto_data <= data_final):
                        continue
                    proposicao = Proposicao()
                    proposicao.data_apresentacao = self.brasilia_tz.localize(projeto_data)
                    proposicao.ementa = projeto['ementa']
                    proposicao.id = projeto['chave']
                    proposicao.tipo = projeto['tipo']
                    proposicao.numero = '{}{}'.format(projeto['numero'], projeto['ano'])
                    proposicao.url_documento = (
                        'http://documentacao.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=proje&form=A&nextAction=search&indexSearch=^nTw^lTodos%20os%20campos&exprSearch=P={tipo}{numero}{ano}'.format(
                            tipo=projeto['tipo'],
                            numero=projeto['numero'],
                            ano=projeto['ano']
                        )
                    )
                    proposicao.url_autores = proposicao.url_documento
                    self.relatorio.proposicoes.append(proposicao)
            except Exception as e:
                #TODO
                print(e)

    def obter_parlamentar(self, parlamentar_id):
        for item in self.ver.obterVereadores():
            if str(item['chave']) == parlamentar_id:
                parlamentar = Parlamentar()
                parlamentar.cargo = 'SÃO PAULO'
                parlamentar.nome = item['nome']
                parlamentar.id = str(item['chave'])
                for mandato in item['mandatos']:
                    if mandato['fim'] > datetime.now():
                        parlamentar.partido = mandato['partido']['sigla']
                parlamentar.uf = 'SP'
                parlamentar.foto = \
                    'https://www.99luca11.com/Users/usuario_sem_foto.png'
                self.obter_cargos_parlamentar(item['cargos'])
                self.relatorio.parlamentar = parlamentar
                return parlamentar

    def obter_cargos_parlamentar(self, cargos):
        for cargo in cargos:
            if 'fim' in cargo and cargo['fim'] < datetime.now():
                continue
            orgao = Orgao()
            orgao.nome = cargo['ente']['nome'].replace(u'Comissão - ', '')
            orgao.cargo = cargo['nome']
            orgao.apelido = orgao.nome
            orgao.sigla = orgao.nome
            self.relatorio.orgaos.append(orgao)
    
    def obter_parlamentares(self):
        vereadores = self.ver.obterVereadores()
        lista = []
        for v in vereadores:
            lista.append(
                {
                    'nome': v['nome'],
                    'id': v['chave'],
                    'siglaPartido': v['mandatos'][0]['partido']['sigla']
                }
            )
        return lista
