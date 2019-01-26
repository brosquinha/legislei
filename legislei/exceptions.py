class AppError(Exception):
    """ Base app exception """

    def __init__(self, msg):
        self.message = msg


class ModelError(AppError):
    """ Base model exception """


class InvalidModelId(AppError):
    """ Exceção para Ids de models inválidos """
