# -*- coding: utf-8 -*-
import json
import logging
import os
from datetime import datetime

import pytz
import sentry_sdk
from flask import Flask, g, redirect, render_template, request, url_for
from flask.sessions import SecureCookieSessionInterface
from flask_login import LoginManager, current_user, login_required
from flask_restplus import Api, Namespace
from sentry_sdk.integrations.flask import FlaskIntegration

from legislei import settings
from legislei.exceptions import (AppError, AvaliacoesModuleError,
                                 InvalidModelId, UsersModuleError)
from legislei.house_selector import (casas_estaduais, casas_municipais,
                                     check_if_house_exists, obter_parlamentar,
                                     obter_parlamentares)
from legislei.models.relatorio import Relatorio
from legislei.models.user import User
from legislei.services.avaliacoes import Avaliacao
from legislei.services.inscricoes import Inscricao
from legislei.services.relatorios import Relatorios
from legislei.services.usuarios import Usuario

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.environ.get('APP_SECRET_KEY')
login_manager = LoginManager()
login_manager.init_app(app)
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%SZ%z',
    level=logging.DEBUG if os.environ.get('DEBUG', 'True').lower() == 'true' else logging.INFO
)
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[FlaskIntegration()]
    )


@app.route('/')
def home():
    return render_template('home.html'), 200


class CustomApi(Api):
    @property
    def specs_url(self):
        '''
        The Swagger specifications absolute url (ie. `swagger.json`)

        :rtype: String
        '''
        return url_for(self.endpoint('specs'), _external=False)


rest_api = CustomApi(
    doc="/swagger",
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
        relatorio = Relatorios().verificar_relatorio(
            parlamentar=request.args['parlamentar'],
            data_final=request.args['data'],
            cargo=request.args['parlamentarTipo'],
            periodo=request.args['dias']
        )
        if isinstance(relatorio, Relatorio):
            return modelar_pagina_relatorio(relatorio.to_dict())
        return render_template('relatorio_background.html')
    except AppError as e:
        return render_template(
            'erro.html',
            erro_titulo="500 - Erro interno",
            erro_descricao=e.message
        ), 500
    except (ValueError, KeyError):
        return render_template(
            'erro.html',
            erro_titulo="400 - Requisição incompleta",
            erro_descricao="Parâmetros incompletos ou incorretos."
        ), 400


@app.route('/relatorio/<id>')
def obter_relatorio_por_id(id):
    relatorio = Relatorios().obter_por_id(id)
    if relatorio:
        return modelar_pagina_relatorio(relatorio.to_dict())
    else:
        return render_template(
            'erro.html',
            erro_titulo="Relatório não encontrado",
            erro_descricao="Esse relatório não existe."
        ), 400


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


@app.route('/registrar')
def new_user_page():
    return render_template('registrar.html')


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
