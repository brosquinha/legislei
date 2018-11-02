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
        dep = DeputadosApp()
        return dep.consultar_deputado()
    elif request.form['parlamentarTipo'] == 'vereadores':
        ver = VereadoresApp()
        return ver.consultar_vereador()
    else:
        return 'Selecione um tipo de parlamentar, plz', 400


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
