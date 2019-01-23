from SDKs.CamaraDeputados.entidades import Deputados
from SDKs.CamaraDeputados.mock import Mocker
import unittest

class TestMock(unittest.TestCase):

    def assertExceptionMessage(self, method, exception, message):
        with self.assertRaises(exception) as cm:
            method()
        err = cm.exception
        self.assertEqual(str(err), message)

    def test_assert_called_attrs(self):
        dep = Deputados()
        mock = Mocker(dep)
        mock.add_response('obterTodosDeputados', [], siglaUf='SP')
        dep.obterTodosDeputados(siglaUf='SP')
        mock.assert_no_pending_responses()

    def test_assert_called_attrs_fails(self):
        dep = Deputados()
        mock = Mocker(dep)
        mock.add_response('obterTodosDeputados', [], siglaUf='SP')
        dep.obterTodosDeputados(siglaUf='MG')
        self.assertExceptionMessage(
            mock.assert_no_pending_responses,
            AssertionError,
            "mock(siglaUf='SP') call not found"
        )

    def test_assert_multiple_methods_ok(self):
        dep = Deputados()
        mock = Mocker(dep)
        mock.add_response('obterTodosDeputados', 1, siglaUf='SP')
        mock.add_response('obterTodosDeputados', 2, siglaUf='MG')
        mock.add_response('obterDeputado', 3, dep_id='123')
        mock.add_response('obterTodosDeputados', 4)
        self.assertEqual(dep.obterTodosDeputados(siglaUf='SP'), 1)
        self.assertEqual(dep.obterTodosDeputados(siglaUf='MG'), 2)
        self.assertEqual(dep.obterDeputado(dep_id='123'), 3)
        self.assertEqual(dep.obterTodosDeputados(), 4)
        mock.assert_no_pending_responses()

    def test_assert_multiple_methods_second_call_wrong(self):
        dep = Deputados()
        mock = Mocker(dep)
        mock.add_response('obterTodosDeputados', 1, siglaUf='SP')
        mock.add_response('obterTodosDeputados', 2, siglaUf='RJ')
        mock.add_response('obterDeputado', 3, dep_id='123')
        mock.add_response('obterTodosDeputados', 4)
        self.assertEqual(dep.obterTodosDeputados(siglaUf='SP'), 1)
        self.assertEqual(dep.obterTodosDeputados(siglaUf='MG'), 2)
        self.assertEqual(dep.obterDeputado(dep_id='123'), 3)
        self.assertEqual(dep.obterTodosDeputados(), 4)
        self.assertExceptionMessage(
            mock.assert_no_pending_responses,
            AssertionError,
            "mock(siglaUf='RJ') call not found"
        )

    def test_assert_multiple_methods_one_extra_response(self):
        dep = Deputados()
        mock = Mocker(dep)
        mock.add_response('obterTodosDeputados', 1, siglaUf='SP')
        mock.add_response('obterTodosDeputados', 2, siglaUf='MG')
        mock.add_response('obterDeputado', 3, dep_id='123')
        mock.add_response('obterTodosDeputados', 4)
        mock.add_response('obterTodosDeputados', 5)
        self.assertEqual(dep.obterTodosDeputados(siglaUf='SP'), 1)
        self.assertEqual(dep.obterTodosDeputados(siglaUf='MG'), 2)
        self.assertEqual(dep.obterDeputado(dep_id='123'), 3)
        self.assertEqual(dep.obterTodosDeputados(), 4)
        self.assertExceptionMessage(
            mock.assert_no_pending_responses,
            AssertionError,
            "Expected obterTodosDeputados to be called 4 times; called 3 times only"
        )