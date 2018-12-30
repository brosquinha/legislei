# -*- coding: utf-8 -*-
import os
import json
import settings
from time import time
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import timedelta, datetime
from pytz import timezone
from db import MongoDBClient
from bson.objectid import ObjectId
from model_selector import model_selector, modelos_estaduais, modelos_municipais
from models.relatorio import Relatorio
from models.user import User
from exceptions import ModelError
from send_reports import check_reports_to_send, send_email
from flask import Flask, request, render_template, redirect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from passlib.hash import pbkdf2_sha256


app = Flask(__name__, static_url_path='/static')
app.secret_key = os.environ.get('APP_SECRET_KEY')
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)


def check_and_send_reports():
    return send_reports(check_reports_to_send())


def send_reports(data):
    for item in data:
        reports = []
        for par in item["parlamentares"]:
            reports.append(obter_relatorio(
                parlamentar=par['id'],
                data_final=datetime.now().strftime('%Y-%m-%d'),
                func=model_selector(par['cargo'])().obter_relatorio,
                periodo=item["intervalo"]
            ))
        with app.app_context():
            html_report = render_template(
                'relatorio_deputado_email.out.html',
                relatorios=reports,
                data_final=datetime.now().strftime('%Y-%m-%d'),
                intervalo=item["intervalo"],
                host=os.environ.get('HOST_ENDPOINT')
            )
        send_email(item["email"], html_report)


scheduler = BackgroundScheduler()
scheduler.configure(timezone=timezone('America/Sao_Paulo'))
scheduler.add_job(
    func=check_and_send_reports,
    trigger='cron',
    day_of_week='sat',
    hour='12',
    minute='0',
    second=0,
    day='*',
    month='*'
)


@app.route('/')
def home():
    return render_template('home.html'), 200


@app.route('/consultar')
def consultar():
    return render_template('consultar_form.html'), 200


def modelar_pagina_relatorio(relatorio, template='consulta_deputado.html'):
    if isinstance(relatorio, tuple) and len(relatorio) == 2:
        return relatorio
    return render_template(
        template,
        relatorio=relatorio
    ), 200


def obter_relatorio(parlamentar, data_final, func, periodo):
    """
    Obtém o relatório da função fornecida

    Espera-se que `func` retorne um objeto Relatorio.
    """
    mongo_db = MongoDBClient()
    relatorios_col = mongo_db.get_collection('relatorios')
    relatorio = relatorios_col.find_one({'idTemp': '{}-{}'.format(parlamentar, data_final)})
    if relatorio != None:
        print('Relatorio carregado!')
        relatorio['_id'] = str(relatorio['_id'])
        return relatorio
    else:
        try:
            relatorio = func(
                parlamentar_id=parlamentar,
                data_final=data_final,
                periodo_dias=periodo
            )
            relatorio_dict = relatorio.to_dict()
            relatorio_dict['_id'] = str(relatorios_col.insert_one(
                {
                    **relatorio_dict,
                    **{'idTemp': '{}-{}'.format(parlamentar, data_final)}
                }
            ).inserted_id)
            return relatorio_dict
        except ModelError as e:
            return render_template(
                'erro.html',
                erro_titulo='500 - Serviço indisponível',
                erro_descricao=e.message
            ), 500
        except TypeError as e:
            return render_template(
                'erro.html',
                erro_titulo='500 - Serviço indisponível',
                erro_descricao=str(e)
            ), 500

@app.route('/relatorio')
def consultar_parlamentar():
    modelClass = model_selector(request.args.get('parlamentarTipo'))
    if modelClass:
        return modelar_pagina_relatorio(obter_relatorio(
            parlamentar=request.args.get('parlamentar'),
            data_final=request.args.get('data'),
            func=modelClass().obter_relatorio,
            periodo=request.args.get('dias')
        ))
    else:
        return 'Selecione um tipo de parlamentar, plz', 400


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
    modelClass = model_selector(request.form.get('parlamentarTipo'))
    if modelClass == None:
        return 'Selecione um modelo, plz', 400
    try:
        mongo_client = MongoDBClient()
        inscricoes_col = mongo_client.get_collection('inscricoes')
        parlamentar = modelClass().obter_parlamentar(request.form.get('parlamentar')).to_dict()
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
        return redirect('/minhasAvaliacoes')
    except AttributeError as e:
        print(e)
        return 'Erro do modelo', 500


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


@app.route('/API/relatorio')
def consultar_deputado_api():
    modelClass = model_selector(request.args.get('parlamentarTipo'))
    if modelClass:
        return json.dumps(obter_relatorio(
            parlamentar=request.args.get('parlamentar'),
            data_final=request.args.get('data'),
            func=modelClass().obter_relatorio,
            periodo=request.args.get('dias')
        ))
    else:
        return '{"error": "Cargo não existe"}', 400


@app.route('/API/minhasInscricoes/<model>/<par_id>', methods=['DELETE'])
@login_required
def remover_inscricao(model, par_id):
    modelClass = model_selector(model)
    if modelClass == None:
        return '{"error": "Cargo não existe"}', 400
    try:
        mongo_client = MongoDBClient()
        inscricoes_col = mongo_client.get_collection('inscricoes')
        inscricoes_col.update_one(
            {'email': current_user.user_email},
            {'$pull': {'parlamentares': {'cargo': model, 'id': par_id}}}
        )
        mongo_client.close()
        return "Ok", 200
    except AttributeError:
        return '{"error": "Erro de modelo"}', 500


@app.route('/API/minhasInscricoes/config', methods=['POST'])
@login_required
def alterar_inscricoes_config():
    try:
        periodo = int(request.form.get('periodo'))
        if periodo >= 7 and periodo <= 28:
            mongo_client = MongoDBClient()
            inscricoes_col = mongo_client.get_collection('inscricoes')
            inscricoes_col.update_one({'email': current_user.user_email}, {'$set': {'intervalo': periodo}})
            return "Ok", 200
    except TypeError:
        return '{"error": "Periodo deve ser int"}', 400


@app.route('/API/models/estaduais')
def obter_modelos_estaduais():
    return json.dumps({'models': modelos_estaduais()}), 200


@app.route('/API/models/municipais')
def obter_modelos_municipais():
    return json.dumps({'models': modelos_municipais()}), 200


@app.route('/API/parlamentares/<model>')
def obter_parlamentares(model):
    modelClass = model_selector(model)
    if modelClass == None:
        return '{"error": "Cargo não existe"}', 400
    try:
        return json.dumps(modelClass().obter_parlamentares()), 200
    except AttributeError:
        return '{"error": "Erro de configuração de dados desse cargo"}', 500


@app.route('/API/parlamentares/<model>/<par_id>')
def obter_parlamentar(model, par_id):
    modelClass = model_selector(model)
    if modelClass == None:
        return '{"error": "Cargo não existe"}', 400
    try:
        return modelClass().obter_parlamentar(par_id).to_json(), 200
    except AttributeError:
        return '{"error": "Erro de configuração de dados desse cargo"}', 500


@app.route('/API/relatorios/<model>/<par_id>')
def buscar_relatorios_parlamentar(model, par_id):
    modelClass= model_selector(model)
    if modelClass == None:
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
            'password': pbkdf2_sha256.encrypt(user_psw, rounds=16, salt_size=16),
            'email': user_email
        })
        mongo_client.close()
        return redirect('/login')
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
        return redirect('/minhasAvaliacoes')
    return render_template('login.html', mensagem='Usuário/senha incorretos')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


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
    ), 400


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


if __name__ == '__main__':
    app.debug = os.environ.get('DEBUG', 'True') in ['True', 'true']
    port = int(os.environ.get('PORT', 5000))
    scheduler.start()
    app.run(host='0.0.0.0', port=port, threaded=True)
