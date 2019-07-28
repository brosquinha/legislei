import json
import threading
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

    def verificar_relatorio(self, parlamentar, data_final, cargo, periodo):
        brasilia_tz = pytz.timezone('America/Sao_Paulo')
        data_inicial = datetime.strptime(data_final, '%Y-%m-%d') - timedelta(days=int(periodo))
        relatorio = Relatorio.objects(
            parlamentar__id__=parlamentar,
            parlamentar__cargo=cargo,
            data_final=brasilia_tz.localize(datetime.strptime(data_final, '%Y-%m-%d')),
            data_inicial=brasilia_tz.localize(data_inicial)
        )
        return relatorio.first() if relatorio else None
    
    def obter_relatorio(self, parlamentar, data_final, cargo, periodo):
        relatorio = self.verificar_relatorio(parlamentar, data_final, cargo, periodo)
        if relatorio:
            return relatorio.to_dict()
        else:
            relatorio = house_selector.obter_relatorio(
                parlamentar=parlamentar,
                data_final=data_final,
                model=cargo,
                periodo=periodo
            )
            relatorio.save().reload() # Reload para trazer as datas para UTC
            return relatorio.to_dict()

    def solicitar_geracao_relatorio(self, parlamentar, data_final, cargo, periodo):
        """
        Solicita uma geração de relatório de forma assíncrona (através de threads)

        :return: Um objeto relatório se o relatório solicitado já existir no banco de dados,
        ou um booleano indicando se uma nova thread foi criada para atender a solicação
        :rtype: Relatorio ou bool
        """
        relatorio = self.verificar_relatorio(
            parlamentar=parlamentar,
            data_final=data_final,
            cargo=cargo,
            periodo=periodo
        )
        if relatorio:
            return relatorio
        
        thread_name = '{}{}{}{}'.format(
            parlamentar, cargo, data_final, periodo
        )
        for thread in threading.enumerate():
            if thread.name == thread_name:
                return False
        
        report_generation = threading.Thread(
            target=self.obter_relatorio,
            name=thread_name,
            kwargs={
                'parlamentar': parlamentar,
                'data_final': data_final,
                'cargo': cargo,
                'periodo': periodo
            }
        )
        report_generation.start()
        return True