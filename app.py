# -*- coding: utf-8 -*-
import os
import json
from time import time
from datetime import timedelta, datetime
from models.deputados import DeputadosApp
from models.vereadoresSaoPaulo import VereadoresApp
from exceptions import ModelError
from flask import Flask, request, render_template


app = Flask(__name__, static_url_path='/static')


@app.route('/')
def home():
    return render_template('consultar_form.html'), 200


def modelar_pagina_relatorio(relatorio, template='consulta_deputado.html'):
    return render_template(
        template,
        relatorio=relatorio
    ), 200


def obter_relatorio(parlamentar, data, func, **kwargs):
    try:
        arquivo = open('reports/{}-{}.json'.format(
            parlamentar, data
        ))
        relatorio = json.loads(arquivo.read())
        print('Relatorio carregado!')
        return relatorio
    except FileNotFoundError:
        try:
            relatorio = func(**kwargs)
            if not os.path.exists('reports'):
                os.makedirs('reports')
            arquivo = open(
                'reports/{}-{}.json'.format(parlamentar, data),
                'w+'
            )
            arquivo.write(json.dumps(relatorio))
            arquivo.close()
            return relatorio
        except ModelError as e:
            return render_template(
                'erro.html',
                erro_titulo='500 - Serviço indisponível',
                erro_descricao=e.message
            ), 500


@app.route('/', methods=['POST'])
def consultar_parlamentar():
    if request.form['parlamentarTipo'] == 'deputados':
        dep = DeputadosApp()
        if 'data' not in request.form:
            data_final = datetime.now().strftime('%Y-%m-%d')
        else:
            data_final = request.form['data']
        return modelar_pagina_relatorio(obter_relatorio(
            parlamentar=request.form['deputado'],
            data=data_final,
            func=dep.consultar_deputado,
            deputado_id=request.form['deputado'],
            data_final=data_final,
            periodo_dias=request.form['dias']
        ))
    elif request.form['parlamentarTipo'] == 'vereadores':
        ver = VereadoresApp()
        return ver.consultar_vereador()
    else:
        return 'Selecione um tipo de parlamentar, plz', 400


@app.route('/API/relatorioDeputado')
def consultar_deputado_api():
    dep = DeputadosApp()
    return json.dumps(obter_relatorio(
        parlamentar=request.args.get('deputado'),
        data=request.args.get('data'),
        func=dep.consultar_deputado,
        deputado_id=request.args.get('deputado'),
        data_final=request.args.get('data'),
        periodo_dias=request.args.get('dias')
    )), 200


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
    app.debug = True
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
