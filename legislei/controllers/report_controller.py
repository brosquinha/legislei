import json
import os
from datetime import datetime

import pytz
from flask import request
from flask_login import login_required
from flask_restplus import Resource, abort, fields, reqparse

from legislei.app import current_user, rest_api_v1
from legislei.controllers.dto import reports_dto
from legislei.exceptions import AvaliacoesModuleError
from legislei.house_selector import check_if_house_exists
from legislei.models.relatorio import Relatorio
from legislei.services.avaliacoes import Avaliacao
from legislei.services.relatorios import Relatorios

_reports_query_parser = reqparse.RequestParser()
_reports_query_parser.add_argument('casa', required=True, help="Id de casa legislativa")
_reports_query_parser.add_argument('parlamentar', required=True, help="Id de parlamentar")
_request_report = rest_api_v1.model("RequestReport", {
    'casa': fields.String(description="Id de casa legislativa", required=True),
    'parlamentar': fields.String(description="Id de parlamentar", required=True),
    'data_final': fields.String(description="Data final para o fim do relatório (formato: YYYY-MM-DD)", required=True),
    'intervalo': fields.Integer(description="Intervalo em dias do relatório", required=True)
})
_report_item_rating = rest_api_v1.model("ReportItemRating", {
    'item_id': fields.String(description="Id de item de relatório", required=True),
    'avaliacao': fields.String(description="Avaliação numérica dada ao item", required=True)
})

@rest_api_v1.route("/relatorios/<relatorio_id>")
class Report(Resource):
    @rest_api_v1.doc(
        description="Retorna o relatório informado pelo id",
        responses={400: "Id de relatório inválido"}
    )
    @rest_api_v1.marshal_with(reports_dto)
    def get(self, relatorio_id):
        relatorio = Relatorios().obter_por_id(relatorio_id)
        if relatorio:
            return json.loads(relatorio.to_json())
        else:
            abort(400, message="Id de relatório inválido")


@rest_api_v1.route("/relatorios/<relatorio_id>/avaliacoes")
class ReportRatingList(Resource):
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


@rest_api_v1.route("/relatorios/<relatorio_id>/avaliacoes/<avaliacao_id>")
class ReportRating(Resource):
    @login_required
    @rest_api_v1.doc(
        description="Deleta uma avaliação de usuário",
        security="apikey",
        responses={
            200: 'Sucesso',
            400: 'Parâmetros inválidos',
            401: 'Sem autorização'
        }
    )
    def delete(self, relatorio_id, avaliacao_id):
        try:
            Avaliacao().deletar_avaliacao(avaliacao_id)
            return {'message': 'Avaliação deletada'}, 200
        except AvaliacoesModuleError as e:
            return {'message': 'Id de avaliação inválido'}, 400


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
            abort(400, message="Id de casa legislativa inválido")
        resultado = Relatorios().buscar_por_parlamentar(house, assemblyman)
        return resultado if resultado else []

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

        try:
            datetime.strptime(final_datetime, '%Y-%m-%d')
        except ValueError as e:
            return {
                'errors': {
                    'data_final': 'Should be in %Y-%m-%d format'
                },
                'message': 'Input payload validation failed'
            }, 422

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
