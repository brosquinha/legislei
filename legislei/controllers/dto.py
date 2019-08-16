import pytz
from datetime import datetime

from flask_restplus import fields

from legislei.app import rest_api_v1


class MongoDateTime(fields.DateTime):
    def format(self, value):
        if isinstance(value, str):
            date = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        else:
            date = datetime.fromtimestamp(value['$date']/1000, pytz.UTC)
        brasilia_tz = pytz.timezone('America/Sao_Paulo')
        date = brasilia_tz.normalize(date.replace(tzinfo=pytz.UTC))
        return super().format_iso8601(date)


class MongoId(fields.String):
    def format(self, value):
        if isinstance(value, str):
            return value
        return value['$oid']

class CustomPresence(fields.Raw):
    def format(self, value):
        if value == 0:
            return 'Present'
        elif value == 1:
            return 'Expected absence'
        elif value == 2:
            return 'Absent on expected event'
        elif value == 3:
            return 'Absent on scheduled event'
        return None

assemblymen_dto = rest_api_v1.model("Assemblyman", {
    'id': fields.String(description="Assemblyman id", attribute='id'),
    'name': fields.String(description="Assemblyman name", attribute='nome'),
    'party': fields.String(description="Assemblyman party", attribute='partido'),
    'uf': fields.String(description="Assemblyman's federation unit", attribute='uf'),
    'house': fields.String(description="House id", attribute='cargo'),
    'photo': fields.String(description="Assemblyman's avatar", attribute='foto'),
})
subscription_dto = rest_api_v1.model('Subscription', {
    'interval': fields.Integer(description="Interval in days of subscriptions updates"),
    'assemblymen': fields.List(fields.Nested(assemblymen_dto))
})
rating_dto = rest_api_v1.model("Rating", {
    'assemblyman': fields.Nested(assemblymen_dto, attribute='parlamentar'),
    'score': fields.String(description="Rating's score", attribute='avaliacao'),
    'rated_item': fields.Raw(description="Rated item", attribute='avaliado'),
    'report_id': MongoId(description="Item's report id", attribute='relatorioId')
})
commissions_dto = rest_api_v1.model('Commission', {
    'name': fields.String(description="Commission name", attribute='nome'),
    'initials': fields.String(description="Comission's initials", attribute='sigla'),
    'role': fields.String(description="Assemblyman's role in commission", attribute='cargo'),
    'nickname': fields.String(description="Comission nickname", attribute='apelido')
})
proposition_dto = rest_api_v1.model('Proposition', {
    'id': fields.String(description='Proposition id'),
    'type': fields.String(description='Proposition type', attribute='tipo'),
    'program': fields.String(description="Proposition's program", attribute='ementa'),
    'number': fields.String(description="Proposition's number", attribute='numero'),
    'authors_url': fields.String(description="Proposition's authors URL", attribute='urlAutores'),
    'document_url': fields.String(description="Proposition's document online URL", attribute='urlDocumento'),
    'submission_datetime': MongoDateTime(description="Datetime when proposition was submited by its authors", attribute='dataApresentacao'),
    'vote': fields.String(description="Assemblyman's vote on this proposition", attribute='voto'),
    'ruling': fields.String(description="Proposition's ruling", attribute='pauta')
})
events_dto = rest_api_v1.model('Event', {
    'id': fields.String(description='Event id', attribute='id'),
    'name': fields.String(description="Event official name", attribute='nome'),
    'initial_datetime': MongoDateTime(description='Event official initial datetime', attribute='dataInicial'),
    'final_datetime': MongoDateTime(description='Event official end datetime', attribute='dataFinal'),
    'url': fields.String(description='Event URL', attribute='url'),
    'situation': fields.String(description='Event situation', attribute='situacao'),
    'presence': CustomPresence(description="Assemblyman's presence status", attribute='presenca'),
    'commissions': fields.List(fields.Nested(commissions_dto), attribute='orgaos'),
    'program': fields.List(fields.Nested(proposition_dto), attribute='pautas')
})
reports_dto = rest_api_v1.model('Report', {
    'id': MongoId(description='Report id', attribute='_id'),
    'assemblyman': fields.Nested(assemblymen_dto, attribute='parlamentar'),
    'initial_datetime': MongoDateTime(description="Report's initial datetime", attribute='dataInicial'),
    'final_datetime': MongoDateTime(description="Report's end datetime", attribute='dataFinal'),
    'notice': fields.String(
        description="A notice about how the data was gathered, usually indicating if expected data is missing from Dados Abertos portal",
        attribute='mensagem'
    ),
    'commissions': fields.List(fields.Nested(commissions_dto), attribute='orgaos'),
    'propositions': fields.List(fields.Nested(proposition_dto), attribute='proposicoes'),
    'present_events': fields.List(fields.Nested(events_dto), attribute='eventosPresentes'),
    'absent_events': fields.List(fields.Nested(events_dto), attribute='eventosAusentes'),
    'scheduled_events': fields.List(fields.Nested(events_dto), attribute='eventosPrevistos'),
    'relative_presence': fields.String(description="Assemblyman's presence on expected events", attribute='presencaRelativa'),
    'absolute_presence': fields.String(description="Assemblyman's presence on all events", attribute='presencaTotal'),
    'total_absences_expected_events': fields.Integer(
        description="Total number of assemblyman's absences on expected events",
        attribute='eventosAusentesEsperadosTotal'
    )
})
users_dto = rest_api_v1.model("User", {
    'username': fields.String(description="Username", required=True),
    'email': fields.String(description="Unique user email", required=True),
    'password': fields.String(description="User's password", required=True),
    'password_confirmed': fields.String(description="Password confirmation", required=True),
})
