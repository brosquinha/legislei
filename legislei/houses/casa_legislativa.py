import logging
from datetime import timedelta

from legislei.exceptions import ModelError


class CasaLegislativa():

    def __init__(self):
        self.periodo = {'days': 7}
    
    def obterDataInicial(self, data_final, **kwargs):
        return data_final - timedelta(**kwargs)


    def formatarDatasYMD(self, *args):
        resultado = ()
        for data in args:
            try:
                resultado += ('{}-{:02d}-{:02d}'.format(
                    data.year,
                    data.month,
                    data.day),)
            except Exception as e:
                logging.error("Data inválida: {}".format(e))
        return resultado

        
    def obterDataInicialEFinal(self, data_final):
        data_inicial = self.obterDataInicial(data_final, **self.periodo)
        return self.formatarDatasYMD(data_inicial, data_final)


    def setPeriodoDias(self, periodo_dias):
        try:
            if int(periodo_dias) in range(7, 29):
                self.periodo['days'] = int(periodo_dias)
        except ValueError:
            periodo_dias = 7

    def obter_relatorio(self, parlamentar_id, data_final, periodo_dias):
        """
        Deve ser implementado pelas classes herdeiras
        """
        raise ModelError("obter_relatorio deve ser implementado")

    def obter_parlamentares(self):
        """
        Deve ser implementado pelas classes herdeiras
        """
        raise ModelError("obter_parlamentares deve ser implementado")

    def obter_parlamentar(self, parlamentar_id):
        """
        Deve ser implementado pelas classes herdeiras
        """
        raise ModelError("obter_parlamentar deve ser implementado")
