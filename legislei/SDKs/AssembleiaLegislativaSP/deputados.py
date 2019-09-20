import re

from .base import Base
from .exceptions import ALESPConnectionError

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
        relacao_html = self._obterRelacaoNomesIdSPL()
        for child in self.get_XML("deputados/deputados.xml"):
            if child.tag =="Deputado":
                try:
                    idSPL = child.find("IdSPL").text
                    nome = child.find("NomeParlamentar").text
                    if idSPL == "0":
                        idSPL = self._obterIdSPLDeputadoPorNome(relacao_html, nome)
                        if idSPL == "0":
                            idSPL = self._obterIdSPLDeputadoPorMatricula(
                                child.find("Matricula").text)
                    deputados.append({
                        "id": idSPL,
                        "situacao": child.find("Situacao").text,
                        "nome": child.find("NomeParlamentar").text,
                        "urlFoto": child.find("PathFoto").text,
                        "siglaPartido": child.find("Partido").text
                    })
                except AttributeError:
                    #Algum dos atributos está faltando, o que fazer?
                    pass
        return deputados

    def _obterIdSPLDeputadoPorMatricula(self, matricula):
        """
        Workaround para obter os ids de sistema de alguns deputados que,
        por algum motivo, o XML de deputados não retorna direto ¬¬

        :param matricula: Id de matrícula de deputado
        :type matricula: String
        :return: Id SPL de deputado
        :rtype: String
        """
        r = self.http.request(
            "GET",
            "{}/alesp/deputado/?matricula={}".format(self.api_host, matricula)
        )
        if r.status != 200:
            raise ALESPConnectionError(r)
        else:
            item = re.search(r"\&idAutor\=(\d+)", r.data.decode("ISO-8859-1"))
            if item == None:
                return "0"
            return item.group(1)

    def _obterRelacaoNomesIdSPL(self):
        """
        Obtém página com uma relação entre o nome de deputados
        e seus IdsSPL, para diminuir a quantidade de requisições
        ao servidor da ALESP

        :return: HTML da página de pesquisa de proposições
        :rtype: String
        """
        r = self.http.request(
            "GET",
            "{}/alesp/pesquisa-proposicoes/".format(self.api_host)
        )
        if r.status != 200:
            raise ALESPConnectionError(r)
        else:
            return r.data.decode("ISO-8859-1")

    def _obterIdSPLDeputadoPorNome(self, html, nome):
        """
        Busca da página de pesquisa do site da ALESP o IdSPL
        de um deputado dado seu nome.

        :param html: HTML da página de pesquisa. Ver `__obterRelacaoNomesIdSPL`
        :type html: String
        :param nome: Nome de deputado
        :type nome: String
        :return: IdSPL do deputado
        :rtype: String
        """
        item = re.search(r"value=\"(\d+)\"\>" + nome +"\<", html)
        if item == None:
            return "0"
        return item.group(1)
