import json
from datetime import datetime, timedelta

import pytz

from legislei import house_selector
from legislei.models.relatorio import Relatorio


class Relatorios():

    def obter_por_id(self, relatorio_id):
        return Relatorio.objects(pk=relatorio_id)

    def buscar_por_parlamentar(self, cargo, parlamentar_id):
        return json.loads(Relatorio.objects(
            parlamentar__id__=parlamentar_id,
            parlamentar__cargo=cargo
        ).to_json())

    def obter_relatorio(self, parlamentar, data_final, cargo, periodo):
        brasilia_tz = pytz.timezone('America/Sao_Paulo')
        data_inicial = datetime.strptime(data_final, '%Y-%m-%d') - timedelta(days=int(periodo))
        relatorio = Relatorio.objects(
            parlamentar__id__=parlamentar,
            parlamentar__cargo=cargo,
            data_final=brasilia_tz.localize(datetime.strptime(data_final, '%Y-%m-%d')),
            data_inicial=brasilia_tz.localize(data_inicial)
        )
        if relatorio:
            return relatorio.first().to_dict()
        else:
            relatorio = house_selector.obter_relatorio(
                parlamentar=parlamentar,
                data_final=data_final,
                model=cargo,
                periodo=periodo
            )
            relatorio.save().reload() # Reload para trazer as datas para UTC
            return relatorio.to_dict()
