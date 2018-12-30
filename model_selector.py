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
