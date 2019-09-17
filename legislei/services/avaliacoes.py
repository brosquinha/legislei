import logging

from bson.objectid import ObjectId
from mongoengine.errors import ValidationError

from legislei.exceptions import ItemNotFound, ReportNotFound
from legislei.models.avaliacoes import Avaliacoes
from legislei.models.relatorio import Relatorio


class Avaliacao():

    def avaliar(self, avaliado, avaliacao_valor, email, relatorio_id):
        avaliacao = Avaliacoes()
        try:
            relatorio = Relatorio.objects(pk=relatorio_id).first()
        except ValidationError:
            raise ReportNotFound()
        if relatorio == None:
            raise ReportNotFound()
        for tipo in ['eventosAusentes', 'eventosPresentes', 'proposicoes']:
            for item in relatorio.to_dict()[tipo]:
                if 'id' in item and str(item['id']) == avaliado:
                    avaliacao.avaliado = item
                    break
        if avaliacao.avaliado == {}:
            raise ItemNotFound()
        avaliacao.email = email
        avaliacao.relatorioId = ObjectId(relatorio.pk)
        avaliacao.avaliacao = avaliacao_valor
        avaliacao.parlamentar = relatorio.parlamentar
        avaliacao_existente = Avaliacoes.objects(
            avaliado__id__=avaliacao.avaliado['id'],
            parlamentar__id__=relatorio.parlamentar.id,
            parlamentar__cargo=relatorio.parlamentar.cargo,
            email=email,
            relatorioId=relatorio.pk
        )
        if avaliacao_existente:
            Avaliacoes.objects(pk=avaliacao_existente.first().pk).update_one(
                set__avaliacao=avaliacao['avaliacao']
            )
        else:
            avaliacao.save()

    def deletar_avaliacao(self, avaliacao_id):
        try:
            Avaliacoes.objects(pk=avaliacao_id).first().delete()
        except (ValidationError, AttributeError):
            raise ItemNotFound()
    
    def minhas_avaliacoes(self, cargo, parlamentar, email):
        avaliacoes = Avaliacoes.objects(
            parlamentar__id__=parlamentar,
            parlamentar__cargo=cargo,
            email=email
        )
        return avaliacoes

    def avaliacoes(self, cargo, parlamentar, email):
        avaliacoes = self.minhas_avaliacoes(cargo, parlamentar, email)
        if not len(avaliacoes):
            return None, None, None
        parlamentar_dados = avaliacoes.first().parlamentar  # TODO obter isso de inscricoes
        avaliacoes_dados = {'2': [], '1': [], '-1': [], '-2': []}
        for avaliacao in avaliacoes:
            try:
                avaliacoes_dados[avaliacao.avaliacao].append(
                    avaliacao.to_mongo().to_dict())
            except KeyError:
                logging.error("Avaliação inválida: {}".format(avaliacao))
        nota = (
            10 * len(avaliacoes_dados['2']) +
            len(avaliacoes_dados['1']) -
            len(avaliacoes_dados['-1']) -
            10 * len(avaliacoes_dados['-2'])
        )
        return parlamentar_dados, avaliacoes_dados, nota
