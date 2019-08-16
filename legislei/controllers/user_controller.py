from functools import wraps

from flask import g, request
from flask_restplus import fields, Resource

from legislei.app import current_user, rest_api_v1
from legislei.controllers.dto import users_dto
from legislei.exceptions import UsersModuleError
from legislei.usuarios import Usuario


_access_token_dto = rest_api_v1.model("AccessToken", {
    'username': fields.String(description="Nome de usuário"),
    'senha': fields.String(description="Senha do usuário")
})


@rest_api_v1.route("/usuarios/token_acesso")
class User(Resource):
    @rest_api_v1.doc(
        description="Retorna um token de acesso do usuário para uso da API",
        responses={
            200: 'Sucesso',
            400: 'Faltam parâmetros',
            401: 'Login falhou'
        }
    )
    @rest_api_v1.expect(_access_token_dto, validate=True)
    def post(self):
        username = request.json['username']
        password = request.json['senha']
        if Usuario().login(username, password, False):
            token = Usuario().generate_auth_token(current_user)
            g.login_via_header = True
            return {'token': token.decode('ascii')}
        return {'message': 'Login falhou'}, 401


@rest_api_v1.route("/usuarios")
class UserList(Resource):
    @rest_api_v1.doc(
        description="Cria uma nova conta de usuário",
        responses={
            201: 'Usuário criado',
            400: 'Parâmetros inválidos ou incompletos'
        }
    )
    @rest_api_v1.expect(users_dto, validate=True)
    def post(self):
        try:
            Usuario().registrar(
                nome=request.json['username'].lower(),
                senha=request.json['senha'],
                senha_confirmada=request.json['senha_confirmada'],
                email=request.json['email']
            )
            return {'message': 'Criado'}, 201
        except UsersModuleError as e:
            return {'message': e.message}, 400
