import json

from flask_login import login_required
from flask_restplus import abort, fields, Resource

from legislei.app import current_user, rest_api_v1
from legislei.avaliacoes import Avaliacao
from legislei.controllers.dto import assemblymen_dto, rating_dto
from legislei.exceptions import AppError, InvalidModelId
from legislei.house_selector import obter_parlamentar, obter_parlamentares


@rest_api_v1.route("/parlamentares/<casa>")
class AssemblymenList(Resource):
    @rest_api_v1.doc(
        description="Retorna todos os parlamentaresd de uma dada casa legislativa",
        params={'casa': 'Id de uma casa legislativa'},
        responses={400: 'Id de casa legislativa inválido'}
    )
    @rest_api_v1.marshal_list_with(assemblymen_dto)
    def get(self, casa):
        try:
            return obter_parlamentares(casa), 200
        except InvalidModelId:
            abort(400, message="Id de casa legislativa inválido")
        except AppError as e:
            abort(500, message=str(e))


@rest_api_v1.route("/parlamentares/<casa>/<parlamentar>")
class Assemblymen(Resource):
    @rest_api_v1.doc(
        description="Retorna informações sobre um dado parlamentar de uma dada casa legislativa",
        params={'parlamentar': 'Id de parlamentar', 'casa': 'Id de casa legislativa'},
        responses={400: 'Id de casa legislativa inválido', 422: 'Id de parlamentar inválido'}
    )
    @rest_api_v1.marshal_with(assemblymen_dto)
    def get(self, casa, parlamentar):
        try:
            parlamentar = obter_parlamentar(casa, parlamentar)
            if parlamentar == None:
                abort(422, message='Id de parlamentar inválido')
            return json.loads(parlamentar.to_json()), 200
        except InvalidModelId:
            abort(400, message="Id de casa legislativa inválido")
        except AppError as e:
            abort(500, message=str(e))


@rest_api_v1.route("/parlamentares/<casa>/<parlamentar>/avaliacoes")
class AssemblymenRatings(Resource):
    @login_required
    @rest_api_v1.doc(
        security='apikey',
        params={'parlamentar': 'Id de parlamentar', 'casa': 'Id de casa legislativa'},
        description="Retorna todas as avaliações dadas a um dado parlamentar pelo usuário",
        responses={
            401: 'Sem autorização'
        }
    )
    @rest_api_v1.marshal_list_with(rating_dto)
    def get(self, casa, parlamentar):
        return json.loads(Avaliacao().minhas_avaliacoes(casa, parlamentar, current_user.email).to_json()), 200
