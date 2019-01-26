from .base import Base

class Deputados(Base):
    """
    Cliente para obtenção de dados de deputados estaduais
    """

    def obterTodosDeputados(self):
        """
        Obtém todos os deputados estaduais da atual legislatura

        :return: Lista de deputados
        :rtype: List
        """
        deputados = []
        for child in self.get_XML("deputados/deputados.xml"):
            if child.tag =="Deputado":
                try:
                    deputados.append({
                        "id": child.find("IdSPL").text,
                        "situacao": child.find("Situacao").text,
                        "nome": child.find("NomeParlamentar").text,
                        "urlFoto": child.find("PathFoto").text,
                        "siglaPartido": child.find("Partido").text
                    })
                except AttributeError:
                    #Algum dos atributos está faltando, o que fazer?
                    pass
        return deputados
