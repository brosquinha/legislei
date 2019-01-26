from unittest.mock import Mock, call


class Mocker():
    """
    Mocker para testar aplicações com a lib CâmaraDeputados

    Exemplo::

        from AssembleiaLegislativaSP.deputados import Deputados
        from AssembleiaLegislativaSP.mock import Mocker
        import unittest

        class TestUnit(unittest.TestCase):

            def test_stuff(self):
                deputados = Deputados()
                mock = Mocker(deputados)
                mock.add_response('obterTodosDeputados', [{
                    "id": "123",
                    "nome": "ParlamentarTeste"
                }])

                self.assertIn(deputados.obterTodosDeputados(), {
                    "id": "123",
                    "nome": "ParlamentarTeste"
                })
                mock.assert_no_pending_responses()

    """

    def __init__(self, stub):
        self.obj = stub
        self._methods = {}

    def add_response(self, method_name, response, *args, **kwargs):
        """
        Adiciona um valor de retorno para uma chamada do método `method_name` do objeto mockado.

        Se forem passados mais parâmetros, eles serão usados para verificar se o método \
        `method_name` foi chamado com esses argumentos.

        :param method_name: Nome do método a ser mockado
        :type method_name: String
        :param response: Resposta do método
        :type reponse: any
        """
        if args or kwargs:
            this_args = (args, kwargs)
        else:
            this_args = False
        if not method_name in self._methods:
            self._methods[method_name] = {
                "mock": Mock(side_effect=[response]),
                "calls": [{"response": response, "args": this_args}]
            }
        else:
            self._methods[method_name]["calls"].append(
                {"response": response, "args": this_args})
            self._methods[method_name]["mock"].side_effect = [
                x["response"] for x in self._methods[method_name]["calls"]
            ]
        self.obj.__setattr__(
            method_name,
            self._methods[method_name]["mock"]
        )

    def add_exception(self, method_name, exception, *args, **kwargs):
        """
        Força o método `method_name` do objeto mockado a levantar a exception `exception`

        Se forem passados mais parâmetros, eles serão usados para verificar se o método \
        `method_name` foi chamado com esses argumentos.

        :param method_name: Nome do método a ser mockado
        :type method_name: String
        :param response: Resposta do método
        :type reponse: any
        """
        self.add_response(method_name, exception, *args, **kwargs)

    def assert_no_pending_responses(self):
        """
        Verifica que todas as chamadas registradas no mock foram chamadas
        """
        # print(self._methods)
        for method_name, method_info in self._methods.items():
            for calls in method_info["calls"]:
                m_args = calls["args"]
                # print(method_info["mock"].mock_calls)
                if m_args:
                    self.obj.__getattribute__(method_name).assert_any_call(
                        *m_args[0], **m_args[1])
                else:
                    assert self.obj.__getattribute__(
                        method_name).called == True, "{} not called".format(method_name)
            assert self.obj.__getattribute__(method_name).call_count == len(method_info["calls"]), "Expected {} to be called {} times; called {} times only".format(
                method_name, len(method_info["calls"]), self.obj.__getattribute__(
                    method_name).call_count
            )
