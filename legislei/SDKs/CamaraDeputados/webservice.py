import xml.etree.ElementTree as ET

from .api import Base
from .exceptions import (CamaraDeputadosConnectionError,
                         CamaraDeputadosInvalidResponse)


class Webservice(Base):
    """
    Classe base de operações da antiga API de webservices
    """

    def __init__(self):
        super().__init__()
        self.camara_dos_deputados_endpoint = 'https://www.camara.leg.br/SitCamaraWS/'

    def get_XML(self, path, **kwargs):
        """
        Obtém um XML através de HTTP GET e o processa
        """
        r = self._make_request(
            "GET",
            "{}{}".format(self.camara_dos_deputados_endpoint, path),
            fields=kwargs
        )
        if r.status != 200:
            raise CamaraDeputadosConnectionError('{}{}'.format(r.geturl(), kwargs), r.status)
        else:
            try:
                return ET.fromstring(r.data.decode('utf-8'))
            except ET.ParseError:
                raise CamaraDeputadosInvalidResponse()

    def get_element_attr(self, elem, attr):
        """
        Obtém o atributo especificado de elemento, se existir

        Se o atributo não existir, retorna None

        :param elem: Elemento XML
        :type elem: Element
        :param attr: Nome de atributo
        :type attr: String

        :return: Conteúdo do atributo
        :rtype: String
        """
        return elem.attrib[attr].strip() if attr in elem.attrib else None
