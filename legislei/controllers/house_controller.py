from flask_restplus import fields, Resource

from legislei.app import rest_api_v1
from legislei.house_selector import casas_estaduais, casas_municipais

_response_model = rest_api_v1.model('HouseList', {
    'casas': fields.List(fields.String(description='House id')),
})

@rest_api_v1.route("/casas/estados")
class StatesHouses(Resource):
    @rest_api_v1.doc(
        description="Retorna todas as casas legislativas estaduais registradas no Legislei",
        model=_response_model
    )
    def get(self):
        return {'casas': casas_estaduais()}, 200

@rest_api_v1.route("/casas/municipios")
class CountiesHouses(Resource):
    @rest_api_v1.doc(
        description="Retorna todas as casas legislativas municipais registradas no Legislei",
        model=_response_model
    )
    def get(self):
        return {'casas': casas_municipais()}, 200
