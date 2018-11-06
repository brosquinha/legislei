# -*- coding: utf-8 -*-
import json
from time import time
from datetime import timedelta, datetime
from deputados import DeputadosApp
from vereadoresSaoPaulo import VereadoresApp
from flask import Flask, request, render_template


app = Flask(__name__, static_url_path='/static')


@app.route('/')
def home():
    return render_template('consultar_form.html'), 200


@app.route('/', methods=['POST'])
def consultar_parlamentar():
    if request.form['parlamentarTipo'] == 'deputados':
        try:
            arquivo = open('reports/{}-{}.json'.format(
                request.form['deputado'], request.form['data']
            ))
            relatorio_deputado = json.loads(arquivo.read())
            print('Relatorio carregado!')
            return render_template(
                'consulta_deputado.html',
                deputado_nome=relatorio_deputado['deputado']['ultimoStatus']['nome'],
                deputado_partido=relatorio_deputado['deputado']['ultimoStatus']['siglaPartido'],
                deputado_uf=relatorio_deputado['deputado']['ultimoStatus']['siglaUf'],
                deputado_img=relatorio_deputado['deputado']['ultimoStatus']['urlFoto'],
                data_inicial=relatorio_deputado['dataInicial'],
                data_final=relatorio_deputado['dataFinal'],
                presenca=relatorio_deputado['presencaTotal'],
                presenca_relativa=relatorio_deputado['presencaRelativa'],
                total_eventos_ausentes=relatorio_deputado['eventosAusentesTotal'],
                orgaos=relatorio_deputado['orgaos'],
                orgaos_nome=relatorio_deputado['orgaosNomes'],
                eventos=relatorio_deputado['eventosPresentes'],
                todos_eventos=relatorio_deputado['eventosAusentes'],
                eventos_previstos=relatorio_deputado['eventosPrevistos'],
                proposicoes_deputado=relatorio_deputado['proposicoes'],
                json_data=relatorio_deputado
            ), 200
        except FileNotFoundError:
            dep = DeputadosApp()
            return dep.consultar_deputado_html(
                deputado_id=request.form['deputado'],
                data_final=request.form['data'] if 'data' in request.form else None
            )
    elif request.form['parlamentarTipo'] == 'vereadores':
        ver = VereadoresApp()
        return ver.consultar_vereador()
    else:
        return 'Selecione um tipo de parlamentar, plz', 400


@app.route('/API/relatorioDeputado')
def consultar_deputado_api():
    try:
        arquivo = open('reports/{}-{}.json'.format(
            request.args.get('deputado'), request.args.get('data')
        ))
        relatorio_deputado = arquivo.read()
        print('Relatorio carregado!')
        return relatorio_deputado, 200
    except FileNotFoundError:
        dep = DeputadosApp()
        return dep.consultar_deputado_json(
            deputado_id=request.args.get('deputado'),
            data_final=request.args.get('data')
        )


@app.route('/deputados')
def obterDeputados():
    dep = DeputadosApp()
    return dep.obterDeputados()


@app.route('/vereadores')
def obterVereadores():
    ver = VereadoresApp()
    return ver.obterVereadoresAtuais()


@app.errorhandler(500)
def server_error(e):
    return render_template(
        'erro.html',
        erro_titulo="500 - Erro interno do servidor",
        erro_descricao="Yep... cometemos um erro, precisamos corrigir. Sorry."
    ), 500


@app.errorhandler(404)
def not_found(e):
    return render_template(
        'erro.html',
        erro_titulo="404 - Página não encontrada",
        erro_descricao="O clássico. Definitivamente esse recurso não existe."
    ), 404


@app.errorhandler(400)
def client_error(e):
    return render_template(
        'erro.html',
        erro_titulo="404 - Erro do cliente",
        erro_descricao="Aeow, tu não estás fazendo a requisição do jeito certo."
    ), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
