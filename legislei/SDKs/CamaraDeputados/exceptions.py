class CamaraDeputadosError(Exception):
    """
    Exceção base da biblioteca da Câmara dos Deputados

    Todas as exceções dessa biblioteca herdam dessa exceção. Dessa forma, \
    pode-se utilizá-la para capturar qualquer exceção de um método. Exemplo::

        dep = Deputados()
        try:
            deputados = []
            for pagina in dep.obterTodosDeputados():
                for deputado in pagina:
                    deputados.append(deputados)
        except CamaraDeputadosError as e:
            print("Ocorreu um erro com a chadama da API da Câmara dos Deputados")
            print(e)
    """


class CamaraDeputadosConnectionError(CamaraDeputadosError):
    """
    Exceção para erros de conexão com o endpoint da API Dados Abertos da Câmara \
    dos Deputados
    """

    def __init__(self, url, status_code):
        super().__init__("Could not connect to {}, received {}".format(
            url, status_code
        ))


class CamaraDeputadosInvalidResponse(CamaraDeputadosError):
    """
    Exceção para má formatação da resposta do endpoint da API Dados Abertos da \
    Câmara dos Deputados
    """

    def __init__(self, data):
        super().__init__("Could not parse {} response".format(data))