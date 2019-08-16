import json

from flask_login import login_required
from flask_restplus import abort, fields, Resource

from legislei.app import current_user, rest_api_v1
from legislei.avaliacoes import Avaliacao
from legislei.controllers.dto import assemblymen_dto, rating_dto
from legislei.exceptions import AppError, InvalidModelId
from legislei.house_selector import obter_parlamentar, obter_parlamentares


@rest_api_v1.route("/assemblymen/<house>/")
class AssemblymenList(Resource):
    @rest_api_v1.doc(
        description="Gets all assemblymen of given legislative house",
        params={'house': 'A legislative house ID'},
        responses={400: 'Invalid house id'}
    )
    @rest_api_v1.marshal_list_with(assemblymen_dto)
    def get(self, house):
        try:
            return obter_parlamentares(house), 200
        except InvalidModelId:
            abort(400, message="Invalid house id")
        except AppError as e:
            abort(500, message=str(e))


@rest_api_v1.route("/assemblymen/<house>/<assemblyman>/")
class Assemblymen(Resource):
    @rest_api_v1.doc(
        description="Gets information about given assemblyman of given legislative house",
        params={'assemblyman': 'An assemblyman ID', 'house': 'A legislative house ID'},
        responses={400: 'Invalid house id', 422: 'Invalid assemblyman id'}
    )
    @rest_api_v1.marshal_with(assemblymen_dto)
    def get(self, house, assemblyman):
        try:
            parlamentar = obter_parlamentar(house, assemblyman)
            if parlamentar == None:
                return {'error': 'Invalid assemblyman id'}, 422
            return json.loads(parlamentar.to_json()), 200
        except InvalidModelId:
            return {"error": "Invalid house id"}, 400
        except AppError as e:
            return {"error": str(e)}, 500


@rest_api_v1.route("/assemblymen/<house>/<assemblyman>/ratings")
class AssemblymenRatings(Resource):
    @login_required
    @rest_api_v1.doc(
        security='apikey',
        params={'assemblyman': 'An assemblyman ID', 'house': 'A legislative house ID'},
        description="Gets all ratings given to an assemblyman by the current user",
        responses={
            200: 'Success',
            401: 'Unauthorized'
        }
    )
    @rest_api_v1.marshal_list_with(rating_dto)
    def get(self, house, assemblyman):
        return json.loads(Avaliacao().minhas_avaliacoes(house, assemblyman, current_user.email).to_json()), 200


def _select_dto_attribute(obj, list):
    """
    Private helper to select DTO property based
    on possible attribute list

    :param obj: Object to be marshelled
    :type obj: Dict
    :param list: List of possible attribute names
    :type list: List
    :return: Object value
    :rtype: Any
    """
    for l in list:
        if l in obj:
            return obj[l]