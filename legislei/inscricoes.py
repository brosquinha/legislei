from legislei.house_selector import obter_parlamentar
from legislei.models.inscricoes import Inscricoes

class Inscricao():

    def obter_todas_inscricoes(self):
        return Inscricoes.objects()
    
    def obter_minhas_inscricoes(self, email):
        inscricoes = Inscricoes.objects(email=email)
        if inscricoes:
            return inscricoes.first().parlamentares, inscricoes.first().intervalo
        else:
            return [], 7

    def nova_inscricao(self, cargo, parlamentar_id, email):
        parlamentar = obter_parlamentar(cargo, parlamentar_id)
        inscricoes = Inscricoes.objects(email=email)
        if inscricoes:
            inscricao = inscricoes.first()
            inscricao.parlamentares.append(parlamentar)
            inscricao.save()
        else:
            inscricao = Inscricoes(email=email, parlamentares=[parlamentar], intervalo=7)
            inscricao.save()

    def remover_inscricao(self, cargo, parlamentar_id, email):
        Inscricoes.objects(email=email).update_one(
            pull__parlamentares={'cargo': cargo, 'id': parlamentar_id})

    def alterar_configs(self, periodo, email):
        if periodo >= 7 and periodo <= 28:
            Inscricoes.objects(email=email).update_one(set__intervalo=periodo)
