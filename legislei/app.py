# -*- coding: utf-8 -*-
import json
import pytz
import os
from datetime import datetime

from flask import Flask, g, redirect, render_template, request
from flask.sessions import SecureCookieSessionInterface
from flask_login import LoginManager, current_user, login_required
from flask_restplus import Api, Namespace

from legislei import settings
from legislei.avaliacoes import Avaliacao
from legislei.exceptions import AppError, AvaliacoesModuleError, InvalidModelId, UsersModuleError
from legislei.house_selector import (casas_estaduais, casas_municipais,
                                     check_if_house_exists, obter_parlamentar,
                                     obter_parlamentares)
from legislei.inscricoes import Inscricao
from legislei.models.relatorio import Relatorio
from legislei.models.user import User
from legislei.relatorios import Relatorios
from legislei.usuarios import Usuario

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.environ.get('APP_SECRET_KEY')
login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/')
def home():
    return render_template('home.html'), 200


rest_api = Api(
    doc="/swagger/",
    title="Legislei API",
    version="0.1.0",
    authorizations={
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization'
        }
    }
)
rest_api_v1 = Namespace('v1', description='Legislei API')
rest_api.add_namespace(rest_api_v1, "/v1")
rest_api.init_app(app)


class CustomSessionInterface(SecureCookieSessionInterface):
    """
    Custom session interface for preventing using cookies for REST API
    """
    def save_session(self, *args, **kwargs):
        if g.get('login_via_header'):
            return
        return super().save_session(*args, **kwargs)


app.session_interface = CustomSessionInterface()


@login_manager.request_loader
def load_user_from_request(request):
    token = request.headers.get('Authorization')
    if token:
        user = Usuario().verify_auth_token(token)
        if user:
            return user
    return None


@login_manager.user_loader
def load_user(user_id):
    return Usuario().obter_por_id(user_id)


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
        return modelar_pagina_relatorio(Relatorios().obter_relatorio(
            parlamentar=request.args['parlamentar'],
            data_final=request.args['data'],
            cargo=request.args['parlamentarTipo'],
            periodo=request.args['dias']
        ))
    except AppError as e:
        return render_template(
            'erro.html',
            erro_titulo="500 - Erro interno",
            erro_descricao=e.message
        ), 500
    except KeyError:
        return render_template(
            'erro.html',
            erro_titulo="400 - Requisição incompleta",
            erro_descricao="Ae, faltaram parâmetros."
        ), 400


@app.route('/relatorio/<id>')
def obter_relatorio_por_id(id):
    relatorio = Relatorios().obter_por_id(id)
    if relatorio:
        return modelar_pagina_relatorio(relatorio.first().to_dict())
    else:
        return render_template(
            'erro.html',
            erro_titulo="Relatório não encontrado",
            erro_descricao="Esse relatório não existe."
        ), 400


@app.route('/avaliar', methods=['POST'])
@login_required
def avaliar():
    try:
        relatorio = request.form.get('id')
        avaliacao_valor = request.form.get('avaliacao')
        avaliado = request.form.get('avaliado')
    except KeyError:
        return 'Missing arguments', 400
    try:
        email = current_user.email
        Avaliacao().avaliar(avaliado, avaliacao_valor, email, relatorio)
        return 'Created', 201
    except AvaliacoesModuleError as e:
        return e.message, 400


@app.route('/minhasAvaliacoes')
@login_required
def avaliacoes():
    email = current_user.email
    try:
        cargo = request.args['parlamentarTipo']
        parlamentar = request.args['parlamentar']
    except KeyError:
        parlamentares, intervalo = Inscricao().obter_minhas_inscricoes(email)
        return render_template(
            'avaliacoes_home.html',
            parlamentares=parlamentares,
            periodo=intervalo
        )
    parlamentar_dados, avaliacoes_dados, nota = Avaliacao().avaliacoes(
        cargo, parlamentar, email)
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
        Inscricao().nova_inscricao(
            request.form.get('parlamentarTipo'),
            request.form.get('parlamentar'),
            current_user.email
        )
        return redirect('{}/minhasAvaliacoes'.format(os.environ.get('HOST_ENDPOINT', request.url_root[:-1])))
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
    return json.dumps(Avaliacao().minhas_avaliacoes(cargo, parlamentar, current_user.email).to_json(), default=str), 200


@api_error_handler
@app.route('/API/relatorio')
def consultar_deputado_api():
    # TODO Melhorar obter_relatorio para poder apresentar o erro em JSON, não em template
    try:
        return json.dumps(Relatorios().obter_relatorio(
            parlamentar=request.args['parlamentar'],
            data_final=request.args['data'],
            cargo=request.args['parlamentarTipo'],
            periodo=request.args['dias'],
        ), default=str)
    except AppError as e:
        return json.dumps({'error': e.message}), 500
    except KeyError:
        return json.dumps({'error': 'Missing parameters'}), 400


@api_error_handler
@app.route('/API/minhasInscricoes/<model>/<par_id>', methods=['DELETE'])
@login_required
def remover_inscricao(model, par_id):
    if not check_if_house_exists(model):
        return '{"error": "Cargo não existe"}', 400
    try:
        Inscricao().remover_inscricao(model, par_id, current_user.email)
        return '{"message": "Ok"}', 200
    except AttributeError:
        return '{"error": "Erro de modelo"}', 500


@api_error_handler
@app.route('/API/minhasInscricoes/config', methods=['POST'])
@login_required
def alterar_inscricoes_config():
    try:
        periodo = int(request.form.get('periodo'))
        Inscricao().alterar_configs(periodo, current_user.email)
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
        resultado = Relatorios().buscar_por_parlamentar(model, par_id)
        return json.dumps(resultado, default=str), 200
    except AttributeError: 
        return '{"error": "Erro de configuração de dados desse cargo"}', 500


@app.route('/registrar')
def new_user_page():
    return render_template('registrar.html')


@app.route('/registrar', methods=['POST'])
def new_user():
    try:
        try:
            Usuario().registrar(
                nome=request.form['name'].lower(),
                senha=request.form['password'],
                senha_confirmada=request.form['password_confirmed'],
                email=request.form['email']
            )
            return redirect('{}/login'.format(os.environ.get('HOST_ENDPOINT', request.url_root[:-1])))
        except UsersModuleError as e:
            return render_template('registrar.html', mensagem=e.message)
    except KeyError:
        return render_template('registrar.html', mensagem='Preencha todo o formulário')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    user_name = request.form.get('name')
    user_psw = request.form.get('password')
    remember_me = True if request.form.get('rememberme') else False
    if Usuario().login(user_name, user_psw, remember_me):
        return redirect('{}/minhasAvaliacoes'.format(os.environ.get('HOST_ENDPOINT', request.url_root[:-1])))
    return render_template('login.html', mensagem='Usuário/senha incorretos')


@app.route('/logout')
@login_required
def logout():
    Usuario().logout()
    return redirect('{}/'.format(os.environ.get('HOST_ENDPOINT', request.url_root[:-1])))


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

@app.template_filter('formatDate')
def format_date(date, time=False):
    if not isinstance(date, datetime):
        return date
    brasilia_tz = pytz.timezone('America/Sao_Paulo')
    date = brasilia_tz.normalize(date.replace(tzinfo=pytz.UTC))
    if time:
        return date.strftime("%d/%m/%Y %H:%M")
    else:
        return date.strftime("%d/%m/%Y")
