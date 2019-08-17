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
            return 'Presente'
        elif value == 1:
            return 'Ausência esperada'
        elif value == 2:
            return 'Ausente em evento esperado'
        elif value == 3:
            return 'Ausente em evento programado'
        return None

assemblymen_dto = rest_api_v1.model("Assemblyman", {
    'id': fields.String(description="Id de parlamentar", attribute='id'),
    'nome': fields.String(description="Nome do parlamentar", attribute='nome'),
    'partido': fields.String(description="Partido do parlamentar", attribute='partido'),
    'uf': fields.String(description="Unidade federativa do parlamentar", attribute='uf'),
    'casa': fields.String(description="Id de casa legislativa do parlamentar", attribute='cargo'),
    'foto': fields.String(description="Foto do parlamentar", attribute='foto'),
})
subscription_dto = rest_api_v1.model('Subscription', {
    'intervalo': fields.Integer(description="Intervalo em dias de relatórios das inscrições"),
    'parlamentares': fields.List(fields.Nested(assemblymen_dto))
})
rating_dto = rest_api_v1.model("Rating", {
    'parlamentar': fields.Nested(assemblymen_dto, attribute='parlamentar'),
    'avaliacao': fields.String(description="Avaliação numérica dada ao item", attribute='avaliacao'),
    'item_avaliado': fields.Raw(description="Item avaliado", attribute='avaliado'),
    'relatorio_id': MongoId(description="Id do relatório ao qual o item avaliado pertence", attribute='relatorioId')
})
commissions_dto = rest_api_v1.model('Commission', {
    'nome': fields.String(description="Nome da comissão", attribute='nome'),
    'iniciais': fields.String(description="Iniciais da comissão", attribute='sigla'),
    'cargo': fields.String(description="Cargo do parlamentar na comissão", attribute='cargo'),
    'apelido': fields.String(description="Apelido da comissão", attribute='apelido')
})
proposition_dto = rest_api_v1.model('Proposition', {
    'id': fields.String(description='Id da proposição'),
    'tipo': fields.String(description='Tipo da proposição', attribute='tipo'),
    'ementa': fields.String(description="Ementa da proposição", attribute='ementa'),
    'numero': fields.String(description="Número da proposição", attribute='numero'),
    'url_autores': fields.String(description="URL de autores da proposição", attribute='urlAutores'),
    'url_documentos': fields.String(description="URL do documento da proposição", attribute='urlDocumento'),
    'data_submissao': MongoDateTime(description="Data de apresentação da proposição por seus autores", attribute='dataApresentacao'),
    'voto': fields.String(description="Voto do parlamentar nesta proposição", attribute='voto'),
    'pauta': fields.String(description="Pauta da proposição", attribute='pauta')
})
events_dto = rest_api_v1.model('Event', {
    'id': fields.String(description='Id do evento', attribute='id'),
    'nome': fields.String(description="Nome oficial do evento", attribute='nome'),
    'data_inicial': MongoDateTime(description='Data e hora de início do evento', attribute='dataInicial'),
    'data_final': MongoDateTime(description='Data e hora de término do evento', attribute='dataFinal'),
    'url': fields.String(description='URL do evento', attribute='url'),
    'situacao': fields.String(description='Situação do evento (realizado, cancelado, etc)', attribute='situacao'),
    'presenca': CustomPresence(description="Presença do parlamentar no evento", attribute='presenca'),
    'orgaos': fields.List(fields.Nested(commissions_dto), attribute='orgaos'),
    'pautas': fields.List(fields.Nested(proposition_dto), attribute='pautas')
})
reports_dto = rest_api_v1.model('Report', {
    'id': MongoId(description='Id do relatório', attribute='_id'),
    'parlamentar': fields.Nested(assemblymen_dto, attribute='parlamentar'),
    'data_inicial': MongoDateTime(description="Data inicial do relatório", attribute='dataInicial'),
    'data_final': MongoDateTime(description="Data final do relatório", attribute='dataFinal'),
    'aviso': fields.String(
        description="Um aviso sobre a disponibilidade dos dados para a geração desse relatório. Normalmente presente quando alguns dados esperados não estão disponíveis no portal de Dados Abertos da casa legislativa em questão",
        attribute='mensagem'
    ),
    'orgaos': fields.List(fields.Nested(commissions_dto), attribute='orgaos'),
    'proposicoes': fields.List(fields.Nested(proposition_dto), attribute='proposicoes'),
    'eventos_presentes': fields.List(fields.Nested(events_dto), attribute='eventosPresentes'),
    'eventos_ausentes': fields.List(fields.Nested(events_dto), attribute='eventosAusentes'),
    'eventos_previstos': fields.List(fields.Nested(events_dto), attribute='eventosPrevistos'),
    'presenca_relativa': fields.String(description="Presença em porcentagem do parlamentar levando em conta apenas eventos esperados", attribute='presencaRelativa'),
    'presenca_absoluta': fields.String(description="Presença em porcentagem do parlamentar considerando todos os eventos da semana", attribute='presencaTotal'),
    'total_eventos_ausentes_esperados': fields.Integer(
        description="Número total de eventos esperados que o parlamentar se ausentou",
        attribute='eventosAusentesEsperadosTotal'
    )
})
users_dto = rest_api_v1.model("User", {
    'username': fields.String(description="Nome de usuário único", required=True),
    'email': fields.String(description="Email de usuário único", required=True),
    'senha': fields.String(description="Senha do usuário", required=True),
    'senha_confirmada': fields.String(description="Confirmação de senha", required=True),
})
