# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime, timedelta
from time import time

from apscheduler.schedulers.background import BackgroundScheduler
from bson.objectid import ObjectId
from flask import Flask, redirect, render_template, request
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from passlib.hash import pbkdf2_sha256
from pytz import timezone

from legislei import settings
from legislei.db import MongoDBClient
from legislei.exceptions import AppError, InvalidModelId, ModelError
from legislei.house_selector import (casas_estaduais, casas_municipais,
                                     check_if_house_exists, obter_parlamentar,
                                     obter_parlamentares, obter_relatorio)
from legislei.models.relatorio import Relatorio
from legislei.models.user import User
from legislei.send_reports import check_reports_to_send, send_email

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.environ.get('APP_SECRET_KEY')
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)


@app.route('/')
def home():
    return render_template('home.html'), 200


@app.route('/consultar')
def consultar():
    return render_template('consultar_form.html'), 200


@app.route('/sobre')
def sobre():
    return render_template('sobre.html'), 200


@app.route('/privacidade')
def privacidade():
    return render_template('politica_privacidade.html'), 200


def modelar_pagina_relatorio(relatorio, template='consulta_deputado.html'):
    if isinstance(relatorio, tuple) and len(relatorio) == 2:
        return relatorio
    return render_template(
        template,
        relatorio=relatorio
    ), 200


@app.route('/relatorio')
def consultar_parlamentar():
    try:
        return modelar_pagina_relatorio(obter_relatorio(
            parlamentar=request.args.get('parlamentar'),
            data_final=request.args.get('data'),
            model=request.args.get('parlamentarTipo'),
            periodo=request.args.get('dias')
        ))
    except AppError:
        return render_template(
            'erro.html',
            erro_titulo="400 - Requisição incompleta",
            erro_descricao="Ae, faltaram parâmetros."
        ), 400


@app.route('/relatorio/<id>')
def obter_relatorio_por_id(id):
    mongo_client = MongoDBClient()
    relatorios_col = mongo_client.get_collection('relatorios')
    relatorio = relatorios_col.find_one({'_id': ObjectId(id)})
    mongo_client.close()
    if relatorio:
        return modelar_pagina_relatorio(relatorio)
    else:
        return render_template(
            'erro.html',
            erro_titulo="Relatório não encontrado",
            erro_descricao="Esse relatório não existe."
        ), 400


@app.route('/avaliar', methods=['POST'])
@login_required
def avaliar():
    #POC: melhorar modelagem disso, plz
    relatorio = request.form.get('id')
    avaliacao_valor = request.form.get('avaliacao')
    avaliado = request.form.get('avaliado')
    email = current_user.user_email
    avaliacao = {}
    mongo_client = MongoDBClient()
    avaliacoes_col = mongo_client.get_collection('avaliacoes')
    relatorios_col = mongo_client.get_collection('relatorios')
    relatorio = relatorios_col.find_one({'_id': ObjectId(relatorio)})
    if relatorio == None:
        return 'Report not found', 400
    for tipo in ['eventosAusentes', 'eventosPresentes', 'proposicoes']:
        for item in relatorio[tipo]:
            if 'id' in item and str(item['id']) == avaliado:
                avaliacao['avaliado'] = item
                break
    if not 'avaliado' in avaliacao:
        return 'Item not found', 400
    avaliacao['parlamentar'] = relatorio['parlamentar']
    avaliacao['email'] = email
    avaliacao['relatorioId'] = relatorio['_id']
    avaliacao['avaliacao'] = avaliacao_valor
    avaliacao_existente = avaliacoes_col.find_one({
        'avaliado.id': avaliacao['avaliado']['id'],
        'parlamentar.id': relatorio['parlamentar']['id'],
        'parlamentar.cargo': relatorio['parlamentar']['cargo'],
        'email': email,
        'relatorioId': relatorio['_id']
    })
    if avaliacao_existente:
        avaliacoes_col.update_one(
            {'_id': avaliacao_existente['_id']}, {'$set': {'avaliacao': avaliacao_valor}})
    else:
        avaliacoes_col.insert_one(avaliacao)
    mongo_client.close()
    return 'Created', 201


def minhas_avaliacoes(cargo, parlamentar, email):
    mongo_client = MongoDBClient()
    avaliacoes_col = mongo_client.get_collection('avaliacoes')
    avaliacoes = [i for i in avaliacoes_col.find(
        {
            'parlamentar.id': parlamentar,
            'parlamentar.cargo': cargo,
            'email': current_user.user_email
        }
    )]
    mongo_client.close()
    return avaliacoes


@app.route('/minhasAvaliacoes')
@login_required
def avaliacoes():
    email = current_user.user_email
    try:
        cargo = request.args['parlamentarTipo']
        parlamentar = request.args['parlamentar']
    except KeyError:
        mongo_client = MongoDBClient()
        subscription_col = mongo_client.get_collection('inscricoes')
        inscricoes = subscription_col.find_one({'email': email})
        mongo_client.close()
        return render_template(
            'avaliacoes_home.html',
            parlamentares=inscricoes['parlamentares'] if inscricoes else [],
            periodo=inscricoes['intervalo'] if inscricoes else 7
        )
    avaliacoes = minhas_avaliacoes(cargo, parlamentar, email)
    if not len(avaliacoes):
        return render_template('avaliacoes_parlamentar.html', parlamentar=None)
    parlamentar_dados = avaliacoes[-1]['parlamentar']
    avaliacoes_dados = {'2': [], '1': [], '-1': [], '-2': []}
    for avaliacao in avaliacoes:
        try:
            avaliacoes_dados[avaliacao['avaliacao']].append(avaliacao)
        except KeyError:
            print(avaliacao)
    nota = (
        10 * len(avaliacoes_dados['2']) +
        len(avaliacoes_dados['1']) -
        len(avaliacoes_dados['-1']) -
        10 * len(avaliacoes_dados['-2'])
    )
    return render_template(
        'avaliacoes_parlamentar.html',
        parlamentar=parlamentar_dados,
        avaliacoes=avaliacoes_dados,
        nota=nota
    ), 200


@app.route('/novaInscricao')
@login_required
def nova_inscricao():
    return render_template('nova_inscricao.html')


@app.route('/novaInscricao', methods=['POST'])
@login_required
def nova_inscricao_post():
    try:
        mongo_client = MongoDBClient()
        inscricoes_col = mongo_client.get_collection('inscricoes')
        parlamentar = obter_parlamentar(
            request.form.get('parlamentarTipo'),
            request.form.get('parlamentar')
        ).to_dict()
        resultado_update = inscricoes_col.update_one(
            {'email': current_user.user_email},
            {'$push': {"parlamentares": parlamentar}}
        )
        if resultado_update.modified_count == 0:
            inscricoes_col.insert_one({
                'email': current_user.user_email,
                'intervalo': 7,
                'parlamentares': [parlamentar]
            })
        mongo_client.close()
        return redirect('{}/minhasAvaliacoes'.format(os.environ.get('HOST_ENDPOINT')))
    except AppError as e:
        print(e)
        return 'Erro do modelo', 500


def api_error_handler(func):
    def treat_error(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return json.dumps({'error': str(e)}), 500
    return treat_error


@api_error_handler
@app.route('/API/minhasAvaliacoes')
@login_required
def avaliacoes_api():
    #Por ser API, o método de autenticacao deve ser diferente deste por cookies
    try:
        cargo = request.args['parlamentarTipo']
        parlamentar = request.args['parlamentar']
    except KeyError:
        return json.dumps({'error': 'Missing arguments'}), 400
    return json.dumps(minhas_avaliacoes(cargo, parlamentar, current_user.user_email), default=str), 200


@api_error_handler
@app.route('/API/relatorio')
def consultar_deputado_api():
    # TODO Melhorar obter_relatorio para poder apresentar o erro em JSON, não em template
    try:
        return json.dumps(obter_relatorio(
            parlamentar=request.args.get('parlamentar'),
            data_final=request.args.get('data'),
            model=request.args.get('parlamentarTipo'),
            periodo=request.args.get('dias')
        ))
    except AppError:
        return json.dumps({'error': 'Missing parameters'}), 400


@api_error_handler
@app.route('/API/minhasInscricoes/<model>/<par_id>', methods=['DELETE'])
@login_required
def remover_inscricao(model, par_id):
    if not check_if_house_exists(model):
        return '{"error": "Cargo não existe"}', 400
    try:
        mongo_client = MongoDBClient()
        inscricoes_col = mongo_client.get_collection('inscricoes')
        inscricoes_col.update_one(
            {'email': current_user.user_email},
            {'$pull': {'parlamentares': {'cargo': model, 'id': par_id}}}
        )
        mongo_client.close()
        return '{"message": "Ok"}', 200
    except AttributeError:
        return '{"error": "Erro de modelo"}', 500


@api_error_handler
@app.route('/API/minhasInscricoes/config', methods=['POST'])
@login_required
def alterar_inscricoes_config():
    try:
        periodo = int(request.form.get('periodo'))
        if periodo >= 7 and periodo <= 28:
            mongo_client = MongoDBClient()
            inscricoes_col = mongo_client.get_collection('inscricoes')
            inscricoes_col.update_one({'email': current_user.user_email}, {'$set': {'intervalo': periodo}})
            return json.dumps({"message": "Ok {}".format(periodo)}), 200
    except (TypeError, ValueError):
        return '{"error": "Periodo deve ser int"}', 400


@api_error_handler
@app.route('/API/models/estaduais')
def obter_modelos_estaduais():
    return json.dumps({'models': casas_estaduais()}), 200


@api_error_handler
@app.route('/API/models/municipais')
def obter_modelos_municipais():
    return json.dumps({'models': casas_municipais()}), 200


@api_error_handler
@app.route('/API/parlamentares/<model>')
def obter_parlamentares_api(model):
    try:
        return json.dumps(obter_parlamentares(model)), 200
    except InvalidModelId:
        return '{"error": "Cargo não existe"}', 400
    except AppError as e:
        return json.dumps({"error": str(e)}), 500


@api_error_handler
@app.route('/API/parlamentares/<model>/<par_id>')
def obter_parlamentar_api(model, par_id):
    try:
        return obter_parlamentar(model, par_id).to_json(), 200
    except InvalidModelId:
        return '{"error": "Cargo não existe"}', 400
    except AppError as e:
        return json.dumps({"error": str(e)}), 500


@api_error_handler
@app.route('/API/relatorios/<model>/<par_id>')
def buscar_relatorios_parlamentar(model, par_id):
    if not check_if_house_exists(model):
        return '{"error": "Cargo não existe"}', 400
    try:
        mongo_client = MongoDBClient()
        relatorios_col = mongo_client.get_collection('relatorios')
        relatorios = relatorios_col.find({'parlamentar.cargo': model, 'parlamentar.id': par_id})
        resultado = []
        for relatorio in relatorios:
            resultado.append(relatorio)
        mongo_client.close()
        return json.dumps(resultado, default=str), 200
    except AttributeError: 
        return '{"error": "Erro de configuração de dados desse cargo"}', 500


@app.route('/registrar')
def new_user_page():
    return render_template('registrar.html')


@app.route('/registrar', methods=['POST'])
def new_user():
    #Provavelmente é melhor usar MongoEngine para facilitar isso aqui
    try:
        user_name = request.form['name'].lower()
        user_psw = request.form['password']
        user_email = request.form['email']
        if not(len(user_name) > 3 and len(user_psw) and
                user_psw == request.form['password_confirmed']):
            return render_template('registrar.html', mensagem='Requisitos não atingidos')
        mongo_client = MongoDBClient()
        users_col = mongo_client.get_collection('users')
        if users_col.find_one({'username': user_name}):
            mongo_client.close()
            return render_template('registrar.html', mensagem='Usuário já existe')
        if users_col.find_one({'email': user_email}):
            mongo_client.close()
            return render_template('registrar.html', mensagem='Email já cadastrado')
        users_col.insert_one({
            'username': user_name,
            'password': pbkdf2_sha256.using(rounds=16, salt_size=16).hash(user_psw),
            'email': user_email
        })
        mongo_client.close()
        return redirect('{}/login'.format(os.environ.get('HOST_ENDPOINT')))
    except KeyError:
        return render_template('registrar.html', mensagem='Algo de errado não está certo')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    user_name = request.form.get('name').lower()
    user_psw = request.form.get('password')
    remember_me = True if request.form.get('rememberme') else False
    mongo_client = MongoDBClient()
    users_col = mongo_client.get_collection('users')
    user_data = users_col.find_one({'username': user_name})
    mongo_client.close()
    if user_data and pbkdf2_sha256.verify(user_psw, user_data['password']):
        user = User(str(user_data['_id']), user_data['username'], user_data['email'])
        login_user(user, remember=remember_me)
        return redirect('{}/minhasAvaliacoes'.format(os.environ.get('HOST_ENDPOINT')))
    return render_template('login.html', mensagem='Usuário/senha incorretos')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('{}/'.format(os.environ.get('HOST_ENDPOINT')))


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
        erro_titulo="400 - Erro do cliente",
        erro_descricao="Aeow, tu não estás fazendo a requisição do jeito certo."
    ), 400


@app.errorhandler(401)
def auth_error(e):
    return render_template(
        'erro.html',
        erro_titulo="401 - Não autorizado",
        erro_descricao="Essa página requer usuário autenticado no sistema."
    ), 401


@app.template_filter('cargoNome')
def nome_cargo_filter(model):
    if model in ['BR1', 'BR2']:
        return 'deputado federal'
    if len(model) == 2:
        return 'deputado estadual'
    return 'vereador'


@app.template_filter('cargoCidadeNome')
def nome_cidade_filter(model):
    return model.lower().title()


@app.template_filter('tojsonforced')
def tojson_filter(obj):
    return json.dumps(obj, default=str)
