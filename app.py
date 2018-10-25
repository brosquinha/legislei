# -*- coding: utf-8 -*-
import json
from time import time
from datetime import timedelta, datetime
from deputados import DeputadosApp
from vereadoresSaoPaulo import VereadoresApp
from flask import Flask, request, render_template


app = Flask(__name__)


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
    deputados = []
    for page in dep.dep.obterTodosDeputados():
        for item in page:
            deputados.append(item)
    return json.dumps(deputados), 200


@app.route('/vereadores')
def obterVereadores():
    ver = VereadoresApp()
    return json.dumps(ver.ver.obterVereadores()), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
