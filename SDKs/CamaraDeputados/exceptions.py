class CamaraDeputadosError(Exception):
    """ Basic CamaraDeputados library Exception"""


class CamaraDeputadosConnectionError(CamaraDeputadosError):

    def __init__(self, url, status_code):
        super().__init__("Could not connect to {}, received {}".format(
            url, status_code
        ))


class CamaraDeputadosInvalidResponse(CamaraDeputadosError):

    def __init__(self, data):
        super().__init__("Could not parse {} response".format(data))