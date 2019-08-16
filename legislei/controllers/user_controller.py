from functools import wraps

from flask import g, request
from flask_restplus import fields, Resource

from legislei.app import current_user, rest_api_v1
from legislei.controllers.dto import users_dto
from legislei.exceptions import UsersModuleError
from legislei.usuarios import Usuario


_access_token_dto = rest_api_v1.model("AccessToken", {
    'username': fields.String(description="Username"),
    'password': fields.String(description="User's password")
})


@rest_api_v1.route("/users/access_token")
class User(Resource):
    @rest_api_v1.doc(
        description="Gets user access token for API usage",
        responses={
            200: 'Success',
            400: 'Missing parameters',
            401: 'Login failed'
        }
    )
    @rest_api_v1.expect(_access_token_dto, validate=True)
    def post(self):
        username = request.json['username']
        password = request.json['password']
        if Usuario().login(username, password, False):
            token = Usuario().generate_auth_token(current_user)
            g.login_via_header = True
            return {'token': token.decode('ascii')}
        return {'message': 'Login failed'}, 401


@rest_api_v1.route("/users")
class UserList(Resource):
    @rest_api_v1.doc(
        description="Creates a new user",
        responses={
            201: 'User created',
            400: 'Invalid or missing parameters'
        }
    )
    @rest_api_v1.expect(users_dto, validate=True)
    def post(self):
        try:
            Usuario().registrar(
                nome=request.json['username'].lower(),
                senha=request.json['password'],
                senha_confirmada=request.json['password_confirmed'],
                email=request.json['email']
            )
            return {'message': 'Created'}, 201
        except UsersModuleError as e:
            return {'message': e.message}, 400

# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = request.headers.get('Authorization')
#         if token and Usuario().verify_auth_token(token):
#             return f(*args, **kwargs)
#         return {'message': 'Access token required'}, 401
#     return decorated
