class AppError(Exception):
    """ Base app exception """

    def __init__(self, msg):
        self.message = msg


class ModelError(AppError):
    """ Base model exception """


class InvalidModelId(AppError):
    """ Exceção para Ids de models inválidos """


class UsersModuleError(AppError):
    """ Base users module error """
    message = "Erro do serviço de usuários"


class UsernameOrEmailAlreadyExistis(UsersModuleError):
    """ Username already exists in database """
    message = "Usuário e/ou email já existem"

    def __init__(self):
        super().__init__(self.message)


class RequirementsNotMet(UsersModuleError):
    """ User creation requirements not met exception """
    message = "Requisitos não atingidos"

    def __init__(self):
        super().__init__(self.message)

class InvalidEmail(UsersModuleError):
    """ Invalid email exception """
    message = "Email inválido"

    def __init__(self):
        super().__init__(self.message)

class AvaliacoesModuleError(AppError):
    """ Base avaliacoes module error """
    message = "Erro do serviço de avaliações"

class ReportNotFound(AvaliacoesModuleError):
    """ Report not found exception """
    message = "Report not found"

    def __init__(self):
        super().__init__(self.message)

class ItemNotFound(AvaliacoesModuleError):
    """ Item not found exception """
    message =  "Item not found"

    def __init__(self):
        super().__init__(self.message)

class InscricoesModuleError(AppError):
    """ Inscricoes module error """
    message = "Erro do serviço de inscrições"

class UserDoesNotExist(InscricoesModuleError):
    """ User with given email does not exist exception """
    message = "User with given email does not exist"

    def __init__(self):
        super().__init__(self.message)

class DispositivosModuleError(AppError):
    """ Dispositivos module error """
    message = "Erro do serviço de dispositivos"

class InvalidParametersError(DispositivosModuleError):
    """ Invalid parameters for device """

    def __init__(self, message = "Parâmetros inválidos"):
        self.message = message
        super().__init__(self.message)

class DeviceDoesNotExistError(DispositivosModuleError):
    """ Device does not exist """
    message = "Dispositivo não existe"
