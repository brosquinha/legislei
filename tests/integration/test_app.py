import json
import os
import unittest
import warnings
from datetime import datetime
from unittest.mock import patch

import pytz
from bson import ObjectId
from mongoengine import connect

from .utils import *
from legislei.app import app
from legislei.exceptions import AppError, InvalidModelId
from legislei.models.avaliacoes import Avaliacoes
from legislei.models.inscricoes import Inscricoes
from legislei.models.relatorio import Evento, Orgao, Parlamentar, Proposicao, Relatorio
from legislei.models.user import User


class TestApp(ControllerHelperTester):

    def test_home_page(self):
        actual = self.app.get("/")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(b"Projeto Legislei", actual.data)

    def test_consultar_page(self):
        actual = self.app.get("/consultar")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Consultar político".encode('utf-8'), actual.data)

    def test_relatorio_no_params(self):
        actual = self.app.get("/relatorio")
        self.assertEqual(actual.status_code, 400)

    def test_relatorio_from_db(self):
        actual = self.app.get("/relatorio?parlamentar=123&data=2019-01-07&parlamentarTipo=BR1&dias=7")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(b"ParlamentarTeste", actual.data)

    def test_relatorio_not_in_db(self):
        actual = self.app.get("/relatorio?parlamentar=123&data=2019-01-07&parlamentarTipo=BR3&dias=7")
        self.assertEqual(actual.status_code, 400)

    def test_get_relatorio_by_id(self):
        actual = self.app.get("/relatorio/5c264b5e3a5efd576ecaf48e")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(b"ParlamentarTeste", actual.data)

    def test_get_relatorio_no_relatorio(self):
        actual = self.app.get("/relatorio/4c264b5e3a5efd576ecaf48e")
        self.assertEqual(actual.status_code, 400)
        self.assertIn(u"Relatório não encontrado".encode("utf-8"), actual.data)

    def test_minhas_avaliacoes(self):
        login(self.app, "test", "123")
        actual = self.app.get("/minhasAvaliacoes")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Minhas avaliações".encode('utf-8'), actual.data)
        self.assertIn(b"ParlamentarTeste", actual.data)

    def test_minhas_avaliacoes_parlamentar(self):
        login(self.app, "test", "123")
        actual = self.app.get("/minhasAvaliacoes?parlamentarTipo=BR1&parlamentar=123")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(b"ParlamentarTeste", actual.data)
        self.assertIn(b"Saldo total: 1", actual.data)

    def test_minhas_avaliacoes_parlamentar_sem_avaliacoes(self):
        login(self.app, "test", "123")
        actual = self.app.get("/minhasAvaliacoes?parlamentarTipo=BR1&parlamentar=12345")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Nenhuma avaliação".encode('utf-8'), actual.data)

    def test_nova_inscricao_home(self):
        login(self.app, "test", "123")
        actual = self.app.get("/novaInscricao")
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Nova inscrição".encode('utf-8'), actual.data)

    def test_registrar_home(self):
        actual = self.app.get("/registrar")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("Criar uma conta", actual_data)

    def test_login_home(self):
        actual = self.app.get("/login")
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn("Entrar", actual_data)

    def test_login_ok(self):
        actual = self.app.post(
            "/login",
            data={
                "name": "test",
                "password": "123"
            }, follow_redirects=True
        )
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Minhas inscrições", actual_data)

    def test_login_incorreto(self):
        actual = self.app.post(
            "/login",
            data={
                "name": "test",
                "password": "12345"
            }, follow_redirects=True
        )
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Usuário/senha incorretos", actual_data)

    def test_logout(self):
        login(self.app, "test", "123")
        actual = self.app.get("/logout", follow_redirects=True)
        actual_data = actual.data.decode('utf-8')
        self.assertEqual(actual.status_code, 200)
        self.assertIn(u"Projeto Legislei", actual_data)
