from legislei.exceptions import UserDoesNotExist
from legislei.house_selector import obter_parlamentar
from legislei.models.inscricoes import Inscricoes
from legislei.models.user import User

class Inscricao():

    def obter_todas_inscricoes(self):
        inscricoes = []
        for user in User.objects():
            if user.inscricoes:
                inscricoes.append(user)
        return inscricoes
    
    def obter_minhas_inscricoes(self, email):
        user = User.objects(email=email)
        if not(user):
            raise UserDoesNotExist()
        inscricoes = user.first().inscricoes
        if inscricoes:
            return inscricoes.parlamentares, inscricoes.intervalo
        else:
            return [], 7

    def nova_inscricao(self, cargo, parlamentar_id, email):
        user = User.objects(email=email)
        if not(user):
            raise UserDoesNotExist()
        user = user.first()
        parlamentar = obter_parlamentar(cargo, parlamentar_id)
        inscricoes = user.inscricoes
        if inscricoes:
            user.inscricoes.parlamentares.append(parlamentar)
            user.save()
        else:
            inscricao = Inscricoes(parlamentares=[parlamentar], intervalo=7)
            user.inscricoes = inscricao
            user.save()

    def remover_inscricao(self, cargo, parlamentar_id, email):
        User.objects(email=email).update_one(
            pull__inscricoes__parlamentares={'cargo': cargo, 'id': parlamentar_id})

    def alterar_configs(self, periodo, email):
        if periodo in [7, 14, 21, 28]:
            User.objects(email=email).update_one(set__inscricoes__intervalo=periodo)
