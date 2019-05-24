from .restful import RESTful
from .webservice import Webservice


class Deputados(RESTful):
    """
    Cliente para obtenção de dados de deputados

    Essa classe deve ser instanciada para obtenção de dados referentes \
    aos deputados da atual legisltatura da Câmara dos Deputados. 
    
    Exemplo::
    
        dep = Deputados()
    """

    def __init__(self):
        super(Deputados, self).__init__('deputados')

    def obterTodosDeputados(self, **kwargs):
        """
        Obtém todos os deputados da atual legislatura

        Se não forem fornecidos parâmetros de filtro, somente serão \
        retornados os deputados *em exercício no momento da requisição*.

        Exemplo::

            for pagina in dep.obterTodosDeputados(ordenarPor='nome'):
                for deputado in pagina:
                    print(deputado)

        :param id: Lista de ids de deputados
        :type id: List
        :param nome: Nome de deputado
        :type nome: String
        :param idLegislatura: Ids de legislaturas
        :type idLegislatura: List
        :param siglaUf: Siglas de Unidades Federativas
        :type siglaUf: List
        :param siglaPartido: Siglas de partidos políticos
        :type siglaPartido: List
        :param siglaSexo: "M" para masculino e "F" para feminino
        :type siglaSexo: String
        :param dataInicio: Data de início de um intervalo de tempo, no formato \
        ``AAAA-MM-DD``
        :type dataInicio: String
        :param dataFim: Data de fim de um intervalo de tempo, no formato \
        ``AAAA-MM-DD``
        :type dataFim: String
        :param ordem: Sentido de ordenação—``asc`` para ordem ascendente e ``desc`` \
        para descendente
        :type ordem: String
        :param ordenarPor: Nome do campo pelo qual a lista de deputados deve ser ordenada: \
        ``id``, ``idLegislatura``, ``nome``, ``siglaUF`` ou ``siglaPartido``
        :type ordenarPor: String

        :return: Generator de páginas de lista de dicionário de informações \
        sobre os deputados
        :rtype: Generator
        """
        return self.runThroughAllPages(**kwargs)

    def obterDeputado(self, dep_id):
        """
        Obtém detalhes sobre um deputado

        Obtém informações sobre o deputado identificado pelo id fornecido por ``dep_id``.

        Exemplo::

            deputado = dep.obterDeputado(dep_id)

        :param dep_id: Id de deputado
        :type dep_id: String

        :return: Dicionário de informações de deputado
        :rtype: Dictionary
        """
        return self.getAPISingleRequest(dep_id)

    def obterOrgaosDeputado(self, dep_id, **kwargs):
        """
        Obtém todos os órgãos de um deputado

        Obtém a lista dos órgãos dos quais o deputado identificado por ``dep_id`` \
        faz parte durante o período fornecido pelos parâmetros de filtro. Se não for \
        especificado nenhum parâmetro de tempo, serão retornados os órgãos aos quais o \
        parlamentar faz parte *no momento da requisição*.

        Exemplo::

            for pagina in dep.obterOrgaosDeputado(dep_id, ordem='asc'):
                for orgaos in pagina:
                    print(orgaos)

        :param dep_id: Id de deputado
        :type dep_id: String
        :param dataInicio: Data de início de intervalo de tempo no formato ``AAAA-MM-DD``
        :type dataInicio: String
        :param dataFim: Data de término de intervalo de tempo no formato ``AAAA-MM-DD``
        :type dataFim: String
        :param ordem: Sentido de ordenação—``asc`` para ordem ascendente e ``desc`` \
        para descendente
        :type ordem: String
        :param ordenarPor: Nome de campo pelo qual a lista deve ser ordenada: ``idOrgao``, \
        ``siglaOrgao``, ``nomeOrgao``, ``nomePapel``, ``dataInicio`` e ``dataFim``
        :type ordenarPor: String

        :return: Generator de páginas de lista de órgãos
        :rtype: Generator
        """
        return self.runThroughAllPages(dep_id, 'orgaos', **kwargs)

    def obterEventosDeputado(self, dep_id, **kwargs):
        """ Obtém todos os eventos que um deputado participou

        Obtém todas os eventos nos quais a participação do deputado identificado \
        por ``dep_id`` era ou é prevista.

        Exemplo::

            for pagina in dep.obterEventosDeputado(dep_id, ordem='asc):
                for evento in pagina:
                    print(evento)

        :param dep_id: Id do deputado
        :type dep_id: String
        :param dataInicio: Data de início de intervalo de tempo no formato ``AAAA-MM-DD``
        :type dataInicio: String
        :param dataFim: Data de término de intervalo de tempo no formato ``AAAA-MM-DD``
        :type dataFim: String
        :param ordem: Sentido de ordenação—``asc`` para ordem ascendente e ``desc`` \
        para descendente
        :type ordem: String
        :param ordenarPor: Nome de campo pelo qual a lista deve ser ordenada: ``dataHoraInicio``
        :type ordenarPor: String

        :return: Generator de páginas de lista de eventos
        :rtype: Generator
        """
        return self.runThroughAllPages(dep_id, 'eventos', **kwargs)


class Eventos(RESTful):
    """
    Cliente para obtenção de dados de eventos da Câmara dos Deputados

    Essa classe deve ser instanciada para a obtenção de dados dos eventos \
    da Câmara dos Deputados.

    Exemplo::

        ev = Eventos()
    """

    def __init__(self):
        super(Eventos, self).__init__('eventos')

    def obterTodosEventos(self, **kwargs):
        """
        Obtém todos os eventos da Câmara dos Deputados

        Se nenhum parâmetro de filtro for passado, serão retornados os eventos \
        ocorridos nos dois dias anteriores à data atual, eventos previstos para \
        os próximos dois dias e eventos do próprio dia atual.

        Exemplo::

            for pagina in ev.obterTodosEventos():
                for evento in pagina:
                    print(evento)

        :param id: Identificador numérico de eventos
        :type id: List
        :param codTipoEvento: Identificador numérico do tipo de evento; valores válidos \
        podem ser obtidos através de ``/referencias/tiposEvento``
        :type codTipoEvento: List
        :param codSituacao: Identificador numérico do tipo de situação de evento; valores \
        válidos podem ser obtidos através de ``/referencias/situacoesEvento``
        :type codSituacao: List
        :param codTipoOrgao: Identificador numérico de tipos de órgãos realizadores do \
        evento; valores válidos podem ser obtidos através de ``/referencias/tiposOrgao``
        :type codTipoOrgao: List
        :param dataInicio: Data de início de intervalo de tempo no formato ``AAAA-MM-DD``
        :type dataInicio: String
        :param dataFim: Data de término de intervalo de tempo no formato ``AAAA-MM-DD``
        :type dataFim: String
        :param horaInicio: Hora de início de intervalo de tempo no formato ``hh:mm``
        :type horaInicio: String
        :param horaFim: Hora de término de intervalo de tempo no formato ``hh:mm``
        :type horaFim: String
        :param ordem: Sentido de ordenação—``asc`` para ordem ascendente e ``desc`` \
        para descendente
        :type ordem: String
        :param ordenarPor: Nome de campo pelo qual a lista deve ser ordenada: ``id``, \
        ``dataHoraInicio``, ``dataHoraFim``, ``descricaoSituacao``, ``descricaoTipo`` ou \
        ``titulo``
        :type ordenarPor: String

        :return: Generator de páginas de lista de eventos
        :rtype: Generator
        """
        return self.runThroughAllPages(**kwargs)

    def obterEvento(self, ev_id):
        """
        Obtém informações sobre o evento identificado por ``ev_id``

        Exemplo::

            evento = ev.obterEvento(ev_id)

        :param ev_id: Identificador de um evento
        :type ev_id: String

        :return: Dicionário de informações do evento
        :rtype: Dictionary
        """
        return self.getAPISingleRequest(ev_id)

    def obterDeputadosEvento(self, ev_id):
        """
        Obtém deputados participantes do evento identificado por ``ev_id``

        Se o evento já ocorreu, são retornados os parlamentares que registraram \
        presença no evento. Se o evento ainda está para acontecer, então são retornados \
        deputados cuja presença é prevista.

        Exemplo::

            deputados_presentes = ev.obterDeputadosEvento(ev_id)

        :param ev_id: Identificador de um evento
        :type ev_id: String

        :return: Lista deputados presentes/previstos
        :rtype: List
        """
        return self.getAPISingleRequest(ev_id, 'deputados')

    def obterPautaEvento(self, ev_id):
        """
        Obtém as proposições de um evento de caráter deliberativo

        Se o evento identificado por ``ev_id`` for de caráter deliberativo, \
        é retornada a lista de proposições escolhidos para avaliação parlamentar \
        no evento em questão.

        Exemplo::

            evento_pauta = ev.obterPautaEvento(ev_id)

        :param ev_id: Identificador de um evento
        :type ev_id: String

        :return: Lista de proposições de um evento
        :rtype: List
        """
        return self.getAPISingleRequest(ev_id, 'pauta')


class Proposicoes(RESTful):
    """
    Cliente para obtenção de dados de proposições

    Essa classe deve ser instanciada para a obtenção de dados referentes a \
    proposições da Câmara dos Deputados.

    Exemplo::

        prop = Proposicoes()
    """

    def __init__(self):
        super(Proposicoes, self).__init__('proposicoes')
    
    def obterTodasProposicoes(self, **kwargs):
        """
        Obtém todas as proposições, filtradas pelos argumentos chaveados

        Proposições podem ser projetos de lei, resoluções, medidas provisórias, \
        emendas, pareces. Se não forem passados nenhum filtro, são retornadas \
        todas as proposições que foram apresentadas ou tiveram alguma mudança de \
        situação nos últimos 30 dias.

        Exemplo::

            for pagina in prop.obterTodasProposicoes(dataInicio=inicio, dataFim=fim):
                for proposicao in pagina:
                    print(proposicao)

        :param id: Id de uma ou mais proposições
        :type id: List
        :param siglaTipo: Um ou mais identificador de tipos de proposições; valores \
        válidos podem ser obtidos de ``/referencias/tiposProposicao``
        :type siglaTipo: List
        :param numero: Um ou mais números atribuídos às proposições
        :type numero: List
        :param ano: Um ou mais anos de apresentação das proposições, no formato ``AAAA``
        :type ano: List
        :param idDeputadoAutor: Ids de deputados autores de proposições
        :type idDeputadoAutor: List
        :param autor: Nome de autor de proposições
        :type autor: String
        :param siglaPartidoAutor: Uma ou mais siglas de partidos a que pertençam autores \
        de proposições
        :type siglaPartidoAutor: List
        :param idPartidoAutor: Identificador numérico de partido do autor da proposição
        :type idPartidoAutor: String
        :param siglaUfAutor: Uma ou mais siglas de Unidades Federativas de autores de \
        proposições
        :type siglaUfAutor: List
        :param keywords: Palavras-chaves de proposições
        :type keywords: List
        :param tramitacaoSenado: Verdadeiro para proposições em tramitação no Senado
        :type tramitacaoSenado: Bool
        :param dataInicio: Data de início de intervalo de tempo em que tenha havido \
        tramitação de proposições, no formato ``AAAA-MM-DD``
        :type dataInicio: String
        :param dataFim: Data de término de intervalo de tempo em que tenha havido \
        tramitação de proposições, no formato ``AAAA-MM-DD``
        :type dataFim: String
        :param dataApresentacaoInicio: Data de início de intervalo de tempo em que \
        tenham sido apresentadas as proposições, no formato ``AAAA-MM-DD``
        :type dataApresentacaoInicio: String
        :param dataApresentacaoFim: Data de término de intervalo de tempo em que tenham \
        sido apresentadas as proposições, no formato ``AAAA-MM-DD``
        :type dataApresentacaoFim: String
        :param codSituacao: Identificador numérico de situação de proposição; valores \
        válidos podem ser obtidos em ``/referencias/situacoesProposicao``
        :type codSituacao: List
        :param ordem: Sentido de ordenação—``asc`` para ordem ascendente e ``desc`` \
        para descendente
        :type ordem: String
        :param ordenarPor: Nome de campo pelo qual a lista deve ser ordenada: ``id``, \
        ``codTipo``, ``siglaTipo``, ``numero`` ou ``ano``
        :type ordenarPor: String
        
        :return: Generator de páginas de listas de proposições
        :rtype: Generator
        """
        return self.runThroughAllPages(**kwargs)

    def obterProposicao(self, prop_id):
        """
        Obtém informações sobre a proposição identificada por ``prop_id``

        Exemplo::

            proposicao = prop.obterProposicao(prop_id)

        :param prop_id: Identificador de proposição
        :type prop_id: String

        :return: Dicionário de informações sobre proposição
        :rtype: Dictionary
        """
        return self.getAPISingleRequest(prop_id)

    def obterAutoresProposicao(self, prop_id):
        """
        Obtém autores de proposição identificada por ``prop_id``

        Entre possíveis autores, além de parlamentares, estão instituições dos \
        três poderes e da sociedade civil.

        Exemplo::

            proposicao_autores = prop.obterAutoresProposicao(prop_id)

        :param prop_id: Identificador de proposição
        :type prop_id: String

        :return: Lista de autores de proposição
        :rtype: List
        """
        return self.getAPISingleRequest(prop_id, 'autores')

    def obterTramitacoesProposicao(self, prop_id):
        """
        Obtém o histórico de tramitações da proposição identificada por ``prop_id``

        Exemplo::

            proposicao_tramitacoes = prop.obterTramitacoesProposicao(prop_id)

        :param prop_id: Identificador de proposição
        :type prop_id: String

        :return: Lista de tramitações de proposição
        :rtype: List
        """
        return self.getAPISingleRequest(prop_id, 'tramitacoes')

    def obterVotacoesProposicao(self, tipo, numero, ano):
        """
        Obtém votações pelas quais a proposição identificada por ``prop_id`` já \
        passou

        Exemplo::

            proposicao_votacoes = prop.obterVotacoesProposicao(prop_id)

        :param tipo: Tipo da proposição
        :type tipo: String
        :param numero: Número da proposição
        :type numero: String
        :param ano: Ano da proposição
        :type ano: String

        :return: Lista de votações de proposição
        :rtype: List
        """
        votacoes = []
        webservice = Webservice()
        root = webservice.get_XML(
            "Proposicoes.asmx/ObterVotacaoProposicao",
            tipo=tipo,
            numero=numero,
            ano=ano
        )
        for child in root:
            if child.tag == "Votacoes":
                for v in child:
                    votacao = {
                        "resumo": webservice.get_element_attr(v, "Resumo"),
                        "data": webservice.get_element_attr(v, "Data"),
                        "hora": webservice.get_element_attr(v, "Hora")
                    }
                    votos = v.find("votos")
                    if votos:
                        votacao["votos"] = []
                        for deputado in votos:
                            if deputado.tag == "Deputado":
                                votacao["votos"].append({
                                    "id": webservice.get_element_attr(deputado, "ideCadastro"),
                                    "nome": webservice.get_element_attr(deputado, "Nome"),
                                    "partido": webservice.get_element_attr(deputado, "Partido"),
                                    "uf": webservice.get_element_attr(deputado, "UF"),
                                    "voto": webservice.get_element_attr(deputado, "Voto")
                                })
                    votacoes.append(votacao)
        return votacoes


class Votacoes(RESTful):
    """
    Cliente para obtenção de dados de votações

    Essa classe deve ser instanciada para obtenção de dados de votações da \
    Câmara dos Deputados.

    Exemplo::

        vot = Votacoes()
    """

    def __init__(self):
        super(Votacoes, self).__init__('votacoes')

    def obterVotacao(self, vot_id):
        """
        Obtém informações sobre a votação identificada por ``vot_id``

        Exemplo::

            votacao = vot.obterVotacao(vot_id)

        :param vot_id: Identificador de votação
        :type vot_id: String

        :return: Dicionário de informações de votação
        :rtype: Dictionary
        """
        return self.getAPISingleRequest(vot_id)

    def obterVotos(self, vot_id, **kwargs):
        """
        Obtém votantes e seus votos da votação identificada por ``vot_id``

        Exemplo::

            for pagina in vot.obterVotos(vot_id):
                for voto in pagina:
                    print(voto)

        :param vot_id: Identificador de votação
        :type vot_id: String

        :return: Generator de páginas de votos
        :rtype: Generator
        """
        return self.runThroughAllPages(vot_id, 'votos', **kwargs)