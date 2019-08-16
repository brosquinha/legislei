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
_reports_query_parser.add_argument('house', required=True, help="A legislative house id")
_reports_query_parser.add_argument('assemblyman', required=True, help="Assemblyman id")
_request_report = rest_api_v1.model("RequestReport", {
    'house': fields.String(description="A legislative house id"),
    'assemblyman': fields.String(description="An assemblyman id"),
    'final_datetime': fields.String(description="End datetime of time frame for the report"),
    'interval': fields.Integer(description="Interval in days fo the report")
})
_report_item_rating = rest_api_v1.model("ReportItemRating", {
    'item_id': fields.String(description="A report's item id"),
    'score': fields.String(description="A rating score")
})

@rest_api_v1.route("/reports/<report_id>")
class Report(Resource):
    @rest_api_v1.doc(
        description="Gets a report"
    )
    @rest_api_v1.marshal_with(reports_dto)
    def get(self, report_id):
        return json.loads(Relatorios().obter_por_id(report_id).first().to_json())


@rest_api_v1.route("/reports/<report_id>/ratings")
class ReportRating(Resource):
    @login_required
    @rest_api_v1.doc(
        description="Sends a rating to an item of a given report",
        security="apikey",
        responses={
            201: 'Created',
            400: 'Invalid parameters',
            401: 'Unauthorized'
        }
    )
    @rest_api_v1.expect(_report_item_rating, validate=True)
    def post(self, report_id):
        try:
            email = current_user.email
            item_id = request.json['item_id']
            score = request.json['score']
            Avaliacao().avaliar(item_id, score, email, report_id)
            return {'message': 'Created'}, 201
        except AvaliacoesModuleError as e:
            return {'message': e.message}, 400

@rest_api_v1.route("/reports")
class ReportList(Resource):
    @rest_api_v1.doc(
        description="Gets all reports about a given assemblyman",
        responses={400: 'Invalid house id'}
    )
    @rest_api_v1.expect(_reports_query_parser, validate=True)
    @rest_api_v1.marshal_list_with(reports_dto)
    def get(self):
        _reports_query_parser.parse_args()
        house = request.args.get("house")
        assemblyman = request.args.get("assemblyman")
        if not check_if_house_exists(house):
            return {"message": "Invalid house id"}, 400
        resultado = Relatorios().buscar_por_parlamentar(house, assemblyman)
        return resultado

    @rest_api_v1.doc(
        description="Requests a report for a given assemblyman within a given time frame",
        responses={
            202: 'Report creation accepted',
            201: 'Report created',
            400: 'Missing or invalid parameters'
        }
    )
    @rest_api_v1.expect(_request_report, validate=True)
    def post(self):
        assemblyman = request.json['assemblyman']
        house = request.json['house']
        final_datetime = request.json['final_datetime']
        interval = request.json['interval']

        relatorio = Relatorios().solicitar_geracao_relatorio(
            parlamentar=assemblyman,
            data_final=final_datetime,
            cargo=house,
            periodo=interval
        )
        if isinstance(relatorio, Relatorio):
            return {
                'message': 'Reported already created',
                'url': '{}/v1/reports/{}'.format(
                    os.environ.get('HOST_ENDPOINT', request.url_root[:-1]),
                    relatorio.id
                )
            }, 201
        elif relatorio:
            return {'message': 'Report requested'}, 202
        return {'message': 'Report already being processed'}, 202
