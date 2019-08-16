import json
import os
import pytz
from datetime import datetime

from flask import request
from flask_login import login_required
from flask_restplus import fields, reqparse, Resource

from legislei.app import current_user, rest_api_v1
from legislei.avaliacoes import Avaliacao
from legislei.controllers.dto import reports_dto
from legislei.exceptions import AvaliacoesModuleError
from legislei.house_selector import check_if_house_exists
from legislei.models.relatorio import Relatorio
from legislei.relatorios import Relatorios


_reports_query_parser = reqparse.RequestParser()
_reports_query_parser.add_argument('casa', required=True, help="Id de casa legislativa")
_reports_query_parser.add_argument('parlamentar', required=True, help="Id de parlamentar")
_request_report = rest_api_v1.model("RequestReport", {
    'casa': fields.String(description="Id de casa legislativa"),
    'parlamentar': fields.String(description="Id de parlamentar"),
    'data_final': fields.String(description="Data final para o fim do relatório"),
    'intervalo': fields.Integer(description="Intervalo em dias do relatório")
})
_report_item_rating = rest_api_v1.model("ReportItemRating", {
    'item_id': fields.String(description="Id de item de relatório"),
    'avaliacao': fields.String(description="Avaliação numérica dada ao item")
})

@rest_api_v1.route("/relatorios/<relatorio_id>")
class Report(Resource):
    @rest_api_v1.doc(
        description="Retorna o relatório informado pelo id"
    )
    @rest_api_v1.marshal_with(reports_dto)
    def get(self, relatorio_id):
        return json.loads(Relatorios().obter_por_id(relatorio_id).first().to_json())


@rest_api_v1.route("/relatorios/<relatorio_id>/avaliacoes")
class ReportRating(Resource):
    @login_required
    @rest_api_v1.doc(
        description="Envia uma avaliação a um item de um dado relatório",
        security="apikey",
        responses={
            201: 'Criado',
            400: 'Parâmetros inválidos',
            401: 'Sem autorização'
        }
    )
    @rest_api_v1.expect(_report_item_rating, validate=True)
    def post(self, relatorio_id):
        try:
            email = current_user.email
            item_id = request.json['item_id']
            score = request.json['avaliacao']
            Avaliacao().avaliar(item_id, score, email, relatorio_id)
            return {'message': 'Criado'}, 201
        except AvaliacoesModuleError as e:
            return {'message': e.message}, 400

@rest_api_v1.route("/relatorios")
class ReportList(Resource):
    @rest_api_v1.doc(
        description="Retorna todos os relatórios de um dado parlamentar",
        responses={400: 'Id de casa legislativa inválido'}
    )
    @rest_api_v1.expect(_reports_query_parser, validate=True)
    @rest_api_v1.marshal_list_with(reports_dto)
    def get(self):
        _reports_query_parser.parse_args()
        house = request.args.get("casa")
        assemblyman = request.args.get("parlamentar")
        if not check_if_house_exists(house):
            return {"message": "Id de casa legislativa inválido"}, 400
        resultado = Relatorios().buscar_por_parlamentar(house, assemblyman)
        return resultado

    @rest_api_v1.doc(
        description="Solicita um relatório sobre um dado parlamentar dentro da dada janela de tempo",
        responses={
            202: 'Geração de relatório aceita',
            201: 'Relatório criado',
            400: 'Parâmetros inválidos ou incompletos'
        }
    )
    @rest_api_v1.expect(_request_report, validate=True)
    def post(self):
        assemblyman = request.json['parlamentar']
        house = request.json['casa']
        final_datetime = request.json['data_final']
        interval = request.json['intervalo']

        relatorio = Relatorios().solicitar_geracao_relatorio(
            parlamentar=assemblyman,
            data_final=final_datetime,
            cargo=house,
            periodo=interval
        )
        if isinstance(relatorio, Relatorio):
            return {
                'message': 'Relatório já criado',
                'url': '{}/v1/relatorios/{}'.format(
                    os.environ.get('HOST_ENDPOINT', request.url_root[:-1]),
                    relatorio.id
                )
            }, 201
        elif relatorio:
            return {'message': 'Relatório solicitado'}, 202
        return {'message': 'Relatório já está sendo processado'}, 202
