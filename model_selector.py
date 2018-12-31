from flask import render_template
from db import MongoDBClient
from exceptions import ModelError, AppError, InvalidModelId
from models.deputados import DeputadosApp
from models.deputadosSP import DeputadosALESPApp
from models.vereadoresSaoPaulo import VereadoresApp


model_selector_ref = {
    'BR1': DeputadosApp,
    'SP': DeputadosALESPApp,
    'SÃO PAULO': VereadoresApp
}


def model_selector(selector):
        """
        Obtém o modelo de dados legislativos com base no identificador fornecido

        Regras para determinação de nível federal:
            BR1 e BR2 são federais
            Seletores com exatos dois caracteres são estaduais (siglas dos estados)
            Os demais são municipais (não existem munincípios com nome de dois caracteres)

        :param selector: Identificador padronizado da aplicação (ver regrar acima)
        :type selector: String
        :return: Classe do modelo de dados
        :rtype: ParlamentarApp
        """
        
        return model_selector_ref[selector] if selector in model_selector_ref else None


def check_if_model_exists(model):
    return model in model_selector_ref


def modelos_estaduais():
    """
    Obtém as chaves dos modelos de dados legislativos estaduais
    """
    resultado = []
    for k, v in model_selector_ref.items():
        if len(k) == 2:
            resultado.append(k)
    return resultado


def modelos_municipais():
    """
    Obtém as chaves dos modelos de dados legislativos municipais
    """
    resultado = []
    for k, v in model_selector_ref.items():
        if len(k) > 2 and k not in ['BR1', 'BR2']:
            resultado.append(k)
    return resultado


def obter_relatorio(parlamentar, data_final, model, periodo):
    """
    Obtém o relatório da função fornecida

    :param parlamentar: Id do parlamentar
    :type parlamentar: String
    :param data_final: Data final do período do relatório
    :type data_final: String (mudar isso para datetime)
    :param model: Identificador do modelo de dados legisltaviso
    :type model: String
    :param periodo: Período do relatório em dias
    :type periodo: Int

    :return: Relatório do parlamentar em um período
    :rtype: Dict
    """
    mongo_db = MongoDBClient()
    relatorios_col = mongo_db.get_collection('relatorios')
    relatorio = relatorios_col.find_one({'idTemp': '{}-{}'.format(parlamentar, data_final)})
    if relatorio != None:
        print('Relatorio carregado!')
        relatorio['_id'] = str(relatorio['_id'])
        return relatorio
    else:
        try:
            modelClass = model_selector(model)
            relatorio = modelClass().obter_relatorio(
                parlamentar_id=parlamentar,
                data_final=data_final,
                periodo_dias=periodo
            )
            relatorio_dict = relatorio.to_dict()
            relatorio_dict['_id'] = str(relatorios_col.insert_one(
                {
                    **relatorio_dict,
                    **{'idTemp': '{}-{}'.format(parlamentar, data_final)}
                }
            ).inserted_id)
            return relatorio_dict
        except (AttributeError, TypeError) as e:
            raise AppError(str(e))


def obter_parlamentar(model, par_id):
    """
    Obtém parlamentar identificado por `par_id` do modelo `model`

    :param model: Identificador de modelo de dados legislativos
    :type model: String
    :param par_id: Identificador de parlamentar no modelo
    :type par_id: String

    :return: Parlamentar
    :rtype: Parlamentar
    """

    modelClass = model_selector(model)
    if modelClass == None:
        raise InvalidModelId('{} não existe'.format(model))
    try:
        return modelClass().obter_parlamentar(par_id)
    except AttributeError as e:
        raise AppError(str(e))


def obter_parlamentares(model):
    """
    Obtém todos os parlamentares do modelo `model`

    :param model: Identificador de modelo de dados legislativos
    :type model: String

    :return: Lista de parlamentares
    :rtype: List
    """
    modelClass = model_selector(model)
    if modelClass == None:
        raise InvalidModelId('{} não existe'.format(model))
    try:
        return modelClass().obter_parlamentares()
    except AttributeError as e:
        raise AppError(str(e))
