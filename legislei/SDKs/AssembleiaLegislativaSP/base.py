import logging
import os
import xml.etree.ElementTree as ET
import zipfile
from time import time

import certifi
import urllib3

from .exceptions import ALESPConnectionError, ALESPInvalidResponse


class Base():
    """
    Classe base para requisições da API da Assembleia Legislativa \
    do Estado de São Paulo
    """

    def __init__(self):
        self.api_host = "http://www.al.sp.gov.br"
        self.api_endpoint = "{}/repositorioDados/".format(self.api_host)
        self.http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where()
        )
    
    def get_XML(self, path):
        """
        Método para obter XML de um caminho especificado

        :param path: Caminho de recurso
        :type path: String

        :return: Árvore XML do recurso
        :rtype: Element
        """
        r = self.http.request(
            "GET",
            "{}{}".format(self.api_endpoint, path)
        )
        if r.status != 200:
            raise ALESPConnectionError(r)
        else:
            try:
                return ET.fromstring(r.data.decode('utf-8'))
            except ET.ParseError:
                raise ALESPInvalidResponse()

    def get_child_inner_text(self, elem, tag_name):
        """
        Retorna o conteúdo de texto de uma tag filha do elemento fornecido

        Se não existir a filha com o nome de tag fornecido, None é retornado.

        Exemplo::

            root = self.get_xml("deputados/deputados.xml")
            for child in root:
                print(self.get_child_inner_text(child, "IdDeputado"))
        
        :param elem: Elemento pai
        :type elem: Element
        :param tag_name: Nome da tag da filha
        :type tag_name: String

        :return: Conteúdo de texto da tag filha
        :rtype: String
        """
        return elem.find(tag_name).text if elem.find(tag_name) != None else None

    def get_XML_from_ZIP(self, path, file_name):
        """
        Método para obter XML de um arquivo zip encontrado no caminho especificado

        Esse método escreve no diretório atual o arquivo zip e depois o descomprime, \
        de forma que é necessário que se tenha permissão de escrita e leitura no \
        diretório atual. Os arquivos ficam armazenados na pasta ".ALESP".

        Se o XML especificado por `file_name` já existir na pasta ".ALESP", então \
        ele será reutilizado.

        .. warning::
        
            Este método requer permissões de leitura e escrita do diretório em que \
            é rodado.

        Exemplo::

            base = Base()
            for elem in base.get_XML_from_ZIP(path, 'proposituras.xml'):
                if elem.tag == 'propositura':
                    print(elem)

        :param path: Caminho do arquivo zip
        :type path: String
        :param file_name: Nome do arquivo XML dentro do ZIP
        :type file_name: String

        :return: Generator de todos elementos do XML
        :rtype: Generator
        """
        try:
            return ET.iterparse('.ALESP/{}'.format(file_name))
        except FileNotFoundError:
            r = self.http.request(
                "GET",
                "{}{}".format(self.api_endpoint, path)
            )
            if r.status != 200:
                raise ALESPConnectionError(r)
            else:
                try:
                    logging.debug('Baixando arquivo...')
                    arqName = int(time())
                    arq = open('{}.zip'.format(arqName), 'wb')
                    arq.write(r.data)
                    arq.close()
                    if not os.path.exists('.ALESP'):
                        os.makedirs('.ALESP')
                    with zipfile.ZipFile('{}.zip'.format(arqName), 'r') as zip_ref:
                        zip_ref.extractall('.ALESP')
                    os.remove('{}.zip'.format(arqName))
                    return ET.iterparse('.ALESP/{}'.format(file_name))
                except ET.ParseError:
                    raise ALESPInvalidResponse()
