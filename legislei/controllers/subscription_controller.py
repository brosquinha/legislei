import json

from flask import request
from flask_login import login_required
from flask_restplus import fields, Resource

from legislei.app import current_user, rest_api_v1
from legislei.controllers.dto import subscription_dto
from legislei.exceptions import InvalidModelId
from legislei.house_selector import check_if_house_exists
from legislei.inscricoes import Inscricao


_new_subscription_dto = rest_api_v1.model('AssemblymanId', {
    'casa': fields.String(description="Id de casa legislativa", required=True),
    'parlamentar': fields.String(description="Id de parlamentar", required=True)
})
_subscription_config = rest_api_v1.model('SubscriptionConfig', {
    'intervalo': fields.Integer(
        description="Intervalo em dias de atualização dos relatórios da inscrição (valores válidos: 7, 14, 21 e 28)",
        required=True
    )
})


@rest_api_v1.route("/usuarios/inscricoes")
class SubscriptionList(Resource):
    @login_required
    @rest_api_v1.doc(
        description="Retorna todas as inscrições do usuário",
        security='apikey',
        responses={
            200: 'Sucesso',
            401: 'Sem autorização'
        }
    )
    @rest_api_v1.marshal_with(subscription_dto)
    def get(self):
        parlamentares, intervalo = Inscricao().obter_minhas_inscricoes(current_user.email)
        parlamentares_dicts = [json.loads(x.to_json()) for x in parlamentares]
        return {'intervalo': intervalo, 'parlamentares': parlamentares_dicts}

    @login_required
    @rest_api_v1.doc(
        description="Cria uma nova inscrição de atividades parlamentares",
        security='apikey',
        responses={
            201: 'Criada',
            401: 'Sem autorização',
            400: 'Parâmetros inválidos ou incompletos'
        }
    )
    @rest_api_v1.expect(_new_subscription_dto, validate=True)
    def post(self):
        try:
            Inscricao().nova_inscricao(
                request.json['casa'],
                request.json['parlamentar'],
                current_user.email
            )
            return {'message': 'Criada'}, 201
        except InvalidModelId:
            return {'message': 'Id de casa legislativa inválido'}, 400
    
    @login_required
    @rest_api_v1.doc(
        description="Atualiza as configurações de inscrições do usuário",
        security="apikey",
        responses={
            200: 'Sucesso',
            400: 'Parâmetros inválidos ou incompletos',
            401: 'Sem autorização'
        }
    )
    @rest_api_v1.expect(_subscription_config, validate=True)
    def put(self):
        Inscricao().alterar_configs(request.json["intervalo"], current_user.email)
        return {'message': 'Configurações de inscrições atualizadas'}

@rest_api_v1.route("/usuarios/inscricoes/<casa>/<parlamentar>")
class Subscription(Resource):
    @login_required
    @rest_api_v1.doc(
        description="Deleta uma inscrição",
        security='apikey',
        responses={
            200: 'Sucesso',
            400: 'Parâmetros inválidos',
            401: 'Sem autorização'
        }
    )
    def delete(self, casa, parlamentar):
        if not check_if_house_exists(casa):
            return {'message': 'Id de casa legislativa inválido'}, 400
        Inscricao().remover_inscricao(casa, parlamentar, current_user.email)
        return {'message': 'Inscrição deletada'}, 200
