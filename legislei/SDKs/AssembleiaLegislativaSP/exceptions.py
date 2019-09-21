class ALESPError(Exception):
    """
    Exceção base da biblioteca da Assembleia Legistavida de SP

    Todas as exceções dessa biblioteca herdam dessa exceção. Dessa forma, \
    pode-se utilizá-la para capturar qualquer exceção de um método. Exemplo::

        dep = Deputados()
        try:
            deputados = dep.obterTodosDeputados()
        except ALESPError as e:
            print("Ocorreu um erro com a chadama da API da Assembleia Legislativa SP")
            print(e)
    """

class ALESPConnectionError(ALESPError):
    """
    Exceção para falhas de conexão com o endpoint da API da Assembleia \
    Legislativa do Estado de São Paulo
    """
    def __init__(self, response):
        self.url = response.geturl()
        self.status_code = response.status
        super().__init__("Could not connect to {}, received {}".format(
            self.url, self.status_code
        ))

class ALESPInvalidResponse(ALESPError):
    """
    Exceção para respostas inválidas da API da Assembleia Legislativa. \
    Pode ser um XML mal formatado.
    """