from flask_restplus import fields, Resource

from legislei.app import rest_api_v1
from legislei.house_selector import casas_estaduais, casas_municipais

_response_model = rest_api_v1.model('HouseList', {
    'houses': fields.List(fields.String(description='House id')),
})

@rest_api_v1.route("/houses/states")
class StatesHouses(Resource):
    @rest_api_v1.doc(
        description="Gets all state houses registered in Legislei",
        model=_response_model
    )
    def get(self):
        return {'houses': casas_estaduais()}, 200

@rest_api_v1.route("/houses/counties")
class CountiesHouses(Resource):
    @rest_api_v1.doc(
        description="Gets all counties houses registered in Legislei",
        model=_response_model
    )
    def get(self):
        return {'houses': casas_municipais()}, 200