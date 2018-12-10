from .base import Base

class Proposicoes(Base):
    """
    Cliente para obtenção de proposições da ALESP
    """
    
    def obterTodasProposicoes(self):
        """
        Obtém todas as proposituras da ALESP

        Formato da resposta::

            propositura = {
                'id': String,
                'ementa': String,
                'numero': String,
                'ano': String,
                'dataEntrada': String,
                'dataPublicacao': String
            }

        :return: Generator de proposituras
        :rtype: Generator
        """
        for event, elem in self.get_XML_from_ZIP(
            'processo_legislativo/proposituras.zip',
            'proposituras.xml'
        ):
            if elem.tag == 'propositura':
                yield {
                    'id': self.get_child_inner_text(elem, 'IdDocumento'),
                    'ementa': self.get_child_inner_text(elem, 'Ementa'),
                    'numero': self.get_child_inner_text(elem, 'NroLegislativo'),
                    'ano': self.get_child_inner_text(elem, 'AnoLegislativo'),
                    'dataEntrada': self.get_child_inner_text(elem, 'DtEntradaSistema'),
                    'dataPublicacao': self.get_child_inner_text(elem, 'DtPublicacao')
                }

    def obterTodosAutoresProposicoes(self):
        """
        Obtém todos os autores de proposituras da ALESP

        Formato da resposta::

            autor = {
                'idDocumento': String,
                'idAutor': String,
                'nomeAutor': String
            }

        :return: Generator de autores
        :rtype: Generator
        """
        for event, elem in self.get_XML_from_ZIP(
                'processo_legislativo/documento_autor.zip',
                'documento_autor.xml'
        ):
            if elem.tag == 'DocumentoAutor':
                yield {
                    'idDocumento': self.get_child_inner_text(elem, 'IdDocumento'),
                    'idAutor': self.get_child_inner_text(elem, 'IdAutor'),
                    'nomeAutor': self.get_child_inner_text(elem, 'NomeAutor')
                }
