import json
import warnings
from threading import Thread
from time import sleep
from unittest.mock import patch

from .utils import *
from legislei import controllers

class TestReportController(ControllerHelperTester):
    
    def test_relatorios_relatorio_id_sucesso(self):
        actual = self.app.get("/v1/relatorios/5c264b5e3a5efd576ecaf48e")
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertIn("ParlamentarTeste", str(actual_data))
        self.assertIn("Evento teste", str(actual_data))
        self.assertIn("ÓrgãoTeste", str(actual_data))

    def test_relatorios_relatorio_id_relatorio_inexistente(self):
        actual = self.app.get("/v1/relatorios/inexistente")
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertEqual(actual_data, {"message": "Id de relatório inválido"})

    def test_relatorios_relatorio_id_avaliacoes_sucesso(self):
        login_header = login_api(self.app, "test", "123")
        actual = self.app.post(
            "/v1/relatorios/5c264b5e3a5efd576ecaf48e/avaliacoes",
            data=json.dumps({
                'item_id': '12345',
                'avaliacao': '1'
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 201)
        self.assertEqual(actual_data, {'message': 'Criado'})

    def test_relatorios_relatorio_id_avaliacoes_sem_login(self):
        actual = self.app.post(
            "/v1/relatorios/5c264b5e3a5efd576ecaf48e/avaliacoes",
            data=json.dumps({
                'item_id': '12345',
                'avaliacao': '1'
            }),
            content_type='application/json',
        )
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 401)
        self.assertIn("message", actual_data)

    def test_relatorios_relatorio_id_avaliacoes_parametros_ausentes(self):
        login_header = login_api(self.app, "test", "123")
        actual = self.app.post(
            "/v1/relatorios/5c264b5e3a5efd576ecaf48e/avaliacoes",
            data=json.dumps({
                'avaliacao': '1'
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 400)
        self.assertIn("message", actual_data)
        self.assertIn("errors", actual_data)
        self.assertIn("item_id", actual_data["errors"])

    def test_relatorios_relatorio_id_avaliacoes_item_invalido(self):
        login_header = login_api(self.app, "test", "123")
        actual = self.app.post(
            "/v1/relatorios/5c264b5e3a5efd576ecaf48e/avaliacoes",
            data=json.dumps({
                'item_id': '999',
                'avaliacao': '1'
            }),
            content_type='application/json',
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 400)
        self.assertEqual(actual_data, {'message': 'Item not found'})

    def test_delete_relatorios_relatorio_id_avaliacoes_avaliacao_id_sucesso(self):
        warnings.simplefilter("ignore")
        login_header = login_api(self.app, "test", "123")
        actual = self.app.delete(
            "/v1/relatorios/5c264b5e3a5efd576ecaf48e/avaliacoes/5c5116f5c3acc80004eada0a",
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertEqual(actual_data, {'message': 'Avaliação deletada'})

    def test_delete_relatorios_relatorio_id_avaliacoes_avaliacao_id_avaliacao_inexistente(self):
        login_header = login_api(self.app, "test", "123")
        actual = self.app.delete(
            "/v1/relatorios/5c264b5e3a5efd576ecaf48e/avaliacoes/nao_existe",
            headers=login_header
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertEqual(actual_data, {'message': 'Id de avaliação inválido'})

    def test_delete_relatorios_relatorio_id_avaliacoes_avaliacao_id_sem_login(self):
        actual = self.app.delete(
            "/v1/relatorios/5c264b5e3a5efd576ecaf48e/avaliacoes/5c5116f5c3acc80004eada0a",
        )
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 401)
        self.assertIn("message", actual_data)
    
    def test_get_relatorios_sucesso(self):
        actual = self.app.get("/v1/relatorios?casa=BR1&parlamentar=123")
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertEqual(len(actual_data), 1)
        self.assertIn("ParlamentarTeste", str(actual_data))
        self.assertIn("Evento teste", str(actual_data))
        self.assertIn("ÓrgãoTeste", str(actual_data))

    def test_get_relatorios_parametros_ausentes(self):
        actual = self.app.get("/v1/relatorios?casa=BR1")
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertIn("message", actual_data)
        self.assertIn("errors", actual_data)
        self.assertIn("parlamentar", actual_data["errors"])

    def test_get_relatorios_casa_invalida(self):
        actual = self.app.get("/v1/relatorios?casa=BR3&parlamentar=123")
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 400)
        self.assertEqual(actual_data, {'message': 'Id de casa legislativa inválido'})

    def test_get_relatorios_nenhum_resultado(self):
        actual = self.app.get("/v1/relatorios?casa=BR1&parlamentar=125")
        actual_data = json.loads(actual.data.decode("utf-8"))
        self.assertEqual(actual.status_code, 200)
        self.assertEqual(actual_data, [])

    @patch("legislei.controllers.report_controller.Relatorios.obter_relatorio")
    def test_post_relatorios_sucesso(self, mock_obter_relatorio):
        mock_obter_relatorio.return_value = None
        actual = self.app.post(
            "/v1/relatorios",
            data=json.dumps({
                'parlamentar': '123',
                'casa': 'BR1',
                'data_final': '2019-01-14',
                'intervalo': 7
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 202)
        self.assertEqual(actual_data, {'message': 'Relatório solicitado'})

    def test_post_relatorios_relatorio_existente(self):
        actual = self.app.post(
            "/v1/relatorios",
            data=json.dumps({
                'parlamentar': '123',
                'casa': 'BR1',
                'data_final': '2019-01-07',
                'intervalo': 7
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 201)
        self.assertEqual(actual_data, {
            'message': 'Relatório já criado',
            'url': '/v1/relatorios/5c264b5e3a5efd576ecaf48e'
        })

    def test_post_relatorios_thread_existente(self):
        def fakeLongThread():
            sleep(0.1)
        thread_existente = Thread(
            name='123BR12019-01-147',
            target=fakeLongThread
        )
        thread_existente.start()
        actual = self.app.post(
            "/v1/relatorios",
            data=json.dumps({
                'parlamentar': '123',
                'casa': 'BR1',
                'data_final': '2019-01-14',
                'intervalo': 7
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 202)
        self.assertEqual(actual_data, {'message': 'Relatório já está sendo processado'})

    def test_post_relatorios_parametros_ausentes(self):
        actual = self.app.post(
            "/v1/relatorios",
            data=json.dumps({
                'parlamentar': '123',
                'casa': 'BR1',
                'intervalo': 7
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 400)
        self.assertIn("message", actual_data)
        self.assertIn("errors", actual_data)
        self.assertIn("data_final", actual_data["errors"])

    def test_post_relatorios_data_final_invalida(self):
        actual = self.app.post(
            "/v1/relatorios",
            data=json.dumps({
                'parlamentar': '123',
                'casa': 'BR1',
                'data_final': 'data-invalida',
                'intervalo': 7
            }),
            content_type='application/json'
        )
        actual_data = json.loads(actual.data.decode('utf-8'))
        self.assertEqual(actual.status_code, 422)
        self.assertIn("message", actual_data)
        self.assertIn("errors", actual_data)
        self.assertIn("data_final", actual_data["errors"])
