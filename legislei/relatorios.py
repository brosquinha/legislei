import json
from datetime import datetime

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
        relatorio = Relatorio.objects(
            parlamentar__id__=parlamentar,
            parlamentar__cargo=cargo,
            data_final=datetime.strptime(data_final, '%Y-%m-%d')
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
            relatorio.save()
            return relatorio.to_dict()
