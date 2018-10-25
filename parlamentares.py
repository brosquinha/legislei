from datetime import timedelta

class ParlamentaresApp():

    def obterDataInicial(self, data_final, **kwargs):
        return data_final - timedelta(**kwargs)

        
    def obterDataInicialEFinal(self, data_final):
        data_inicial = self.obterDataInicial(data_final, weeks=1)
        return ('{}-{:02d}-{:02d}'.format(data_inicial.year,
                                        data_inicial.month, data_inicial.day),
                '{}-{:02d}-{:02d}'.format(data_final.year,
                                        data_final.month, data_final.day))
