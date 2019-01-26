from .base import Base

class Comissoes(Base):
    """
    Cliente para obtenção de dados de Comissões Permanentes da ALESP
    """

    def obterMembrosComissoes(self):
        """
        Obtém relação de membros das Comissões Permanentes da ALESP

        :return: Lista de membros
        :rtype: List
        """
        membros = []
        root = self.get_XML("processo_legislativo/comissoes_membros.xml")
        for child in root:
            if child.tag == "MembroComissao":
                membros.append({
                    "dataInicio": self.get_child_inner_text(child, "DataInicio"),
                    "dataFim": self.get_child_inner_text(child, "DataFim"),
                    "idDeputado": self.get_child_inner_text(child, "IdMembro"),
                    "idComissao": self.get_child_inner_text(child, "IdComissao"),
                    "efetivo": self.get_child_inner_text(child, "Efetivo") == "S",
                })
        return membros

    def obterComissoes(self):
        """
        Obtém todas as Comissões Permanentes da ALESP

        :return: Lista de comissões
        :rtype: List
        """
        comissoes = []
        for child in self.get_XML("processo_legislativo/comissoes.xml"):
            if child.tag == "Comissao":
                comissoes.append({
                    "id": self.get_child_inner_text(child, "IdComissao"),
                    "nome": self.get_child_inner_text(child, "NomeComissao"),
                    "sigla": self.get_child_inner_text(child, "SiglaComissao"),
                    "dataFim": self.get_child_inner_text(child, "DataFimComissao")
                })
        return comissoes

    def obterReunioesComissoes(self):
        """
        Obtém todas as reuniões ocorridas ou não das Comissões Permanentes

        :return: Lista de reuniões
        :rtype: List
        """
        reunioes = []
        for child in self.get_XML("processo_legislativo/comissoes_permanentes_reunioes.xml"):
            if child.tag == "ReuniaoComissao":
                reunioes.append({
                    "id": self.get_child_inner_text(child, "IdReuniao"),
                    "idComissao": self.get_child_inner_text(child, "IdComissao"),
                    "idPauta": self.get_child_inner_text(child, "IdPauta"),
                    "situacao": self.get_child_inner_text(child, "Situacao"),
                    "data": self.get_child_inner_text(child, "Data"),
                    "convocacao": self.get_child_inner_text(child, "NrConvocacao")
                })
        return reunioes

    def obterPresencaReunioesComissoes(self):
        """
        Obtém todas as presenças em reuniões de Comissões Permanentes da ALESP

        :return: Presenças em reuniões de comissões
        :rtype: List
        """
        presencas = []
        for child in self.get_XML("processo_legislativo/comissoes_permanentes_presencas.xml"):
            if child.tag == "ReuniaoComissaoPresenca":
                presencas.append({
                    "idDeputado": self.get_child_inner_text(child, "IdDeputado"),
                    "idReuniao": self.get_child_inner_text(child, "IdReuniao"),
                    "idPauta": self.get_child_inner_text(child, "IdPauta"),
                    "idComissao": self.get_child_inner_text(child, "IdComissao")
                })
        return presencas

    def obterVotacoesComissoes(self):
        """
        Obtém todas as votações em Comissões Permanentes da ALESP

        Tipos de votos:

        - F: Favorável
        - C: Contrário
        - S: Com o voto em separado
        - P: Favorável ao projeto
        - T: Contrário ao projeto
        - A: Abstenção
        - B: Branco
        - O: Outros

        :return: Lista de votações
        :rtype: List
        """
        votacoes = []
        for child in self.get_XML("processo_legislativo/comissoes_permanentes_votacoes.xml"):
            if child.tag == "ReuniaoComissaoVotacao":
                votacoes.append({
                    "idDeputado": self.get_child_inner_text(child, "IdDeputado"),
                    "idReuniao": self.get_child_inner_text(child, "IdReuniao"),
                    "idComissao": self.get_child_inner_text(child, "IdComissao"),
                    "idDocumento": self.get_child_inner_text(child, "IdDocumento"),
                    "voto": self.get_child_inner_text(child, "TipoVoto"),
                })
        return votacoes
