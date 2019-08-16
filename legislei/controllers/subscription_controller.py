import json

from flask import request
from flask_login import login_required
from flask_restplus import fields, Resource

from legislei.app import current_user, rest_api_v1
from legislei.controllers.dto import subscription_dto
from legislei.house_selector import check_if_house_exists
from legislei.inscricoes import Inscricao


_new_subscription_dto = rest_api_v1.model('AssemblymanId', {
    'house': fields.String(description="Legislative house id"),
    'assemblyman': fields.String(description="Assemblyman id")
})
_subscription_config = rest_api_v1.model('SubscriptionConfig', {
    'interval': fields.Integer(description="Interval in days of subscriptions updates")
})


@rest_api_v1.route("/users/subscriptions")
class SubscriptionList(Resource):
    @login_required
    @rest_api_v1.doc(
        description="Gets all of current user's subscriptions",
        security='apikey',
        responses={
            200: 'Success',
            401: 'Unauthorized'
        }
    )
    @rest_api_v1.marshal_with(subscription_dto)
    def get(self):
        parlamentares, intervalo = Inscricao().obter_minhas_inscricoes(current_user.email)
        parlamentares_dicts = [json.loads(x.to_json()) for x in parlamentares]
        return {'interval': intervalo, 'assemblymen': parlamentares_dicts}

    @login_required
    @rest_api_v1.doc(
        description="Creates a new assemblyman subscription",
        security='apikey',
        responses={201: 'Created', 401: 'Unauthorized'}
    )
    @rest_api_v1.expect(_new_subscription_dto, validate=True)
    def post(self):
        Inscricao().nova_inscricao(
            request.json['house'],
            request.json['assemblyman'],
            current_user.email
        )
        return {'message': 'Created'}, 201
    
    @login_required
    @rest_api_v1.doc(
        description="Updates user's subscriptions settings",
        security="apikey",
        responses={
            200: 'Success',
            401: 'Unauthorized'
        }
    )
    @rest_api_v1.expect(_subscription_config, validate=True)
    def put(self):
        Inscricao().alterar_configs(request.json["interval"], current_user.email)
        return {'message': 'Subscriptions settings updated'}

@rest_api_v1.route("/users/subscriptions/<house>/<assemblyman>")
class Subscription(Resource):
    @login_required
    @rest_api_v1.doc(
        description="Deletes a subscription",
        security='apikey',
        responses={
            200: 'Success',
            401: 'Unauthorized'
        }
    )
    def delete(self, house, assemblyman):
        if not check_if_house_exists(house):
            return {'message': 'Invalid house id'}, 400
        Inscricao().remover_inscricao(house, assemblyman, current_user.email)
        return {'message': 'Subscription deleted'}, 200