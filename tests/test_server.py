import io
import json
import os
import pathlib
import sys
import threading
import unittest
from http.client import HTTPConnection
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "backend"))
import server
from server import ApiHandler, ThreadingHTTPServer


class ApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None):
        connection = HTTPConnection(self.host, self.port)
        encoded_body = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"} if encoded_body else {}
        connection.request(method, path, encoded_body, headers)
        response = connection.getresponse()
        data = json.loads(response.read())
        connection.close()
        return response.status, data

    def test_hello_endpoint_remains_available(self):
        status, data = self.request("GET", "/api/hello")
        self.assertEqual(status, 200)
        self.assertEqual(data["message"], "Hello, World!")

    def test_analyze_accepts_source_code(self):
        status, data = self.request("POST", "/api/analyze", {"codigo": "x = 10\n"})
        self.assertEqual(status, 200)
        self.assertTrue(data["recebido"])
        self.assertTrue(data["sucesso"])
        self.assertEqual([token["lexema"] for token in data["tokens"]], ["x", "=", "10"])
        self.assertEqual(data["erros"], [])
        self.assertEqual(data["linhas"], 1)
        self.assertEqual(data["caracteres"], 7)
        self.assertTrue(data["lexico"]["sucesso"])
        self.assertTrue(data["sintatico"]["sucesso"])
        self.assertEqual(data["sintatico"]["ast"]["filhos"][0]["tipo"], "ATRIBUICAO")

    def test_analyze_reports_lexical_errors_without_failing_request(self):
        status, data = self.request("POST", "/api/analyze", {"codigo": "x = @"})
        self.assertEqual(status, 200)
        self.assertFalse(data["sucesso"])
        self.assertEqual(data["tokens"][0]["lexema"], "x")
        self.assertEqual(data["erros"][0]["tipo"], "ERRO_LEXICO")
        self.assertFalse(data["sintatico"]["executado"])
        self.assertIsNone(data["sintatico"]["ast"])

    def test_analyze_reports_syntax_errors_without_discarding_tokens(self):
        status, data = self.request("POST", "/api/analyze", {"codigo": "x = 1 +"})
        self.assertEqual(status, 200)
        self.assertTrue(data["lexico"]["sucesso"])
        self.assertFalse(data["sintatico"]["sucesso"])
        self.assertIsNone(data["sintatico"]["ast"])
        self.assertEqual(data["sintatico"]["erros"][0]["tipo"], "ERRO_SINTATICO")
        self.assertEqual([token["lexema"] for token in data["tokens"]], ["x", "=", "1", "+"])

    def test_ai_endpoint_uses_actual_selected_token_and_returns_model_explanation(self):
        ollama_response = io.BytesIO(
            json.dumps({"message": {"content": "10 é um literal inteiro."}}).encode("utf-8")
        )
        with patch("server.urlopen", return_value=ollama_response) as mocked_urlopen:
            status, data = self.request(
                "POST",
                "/api/ia/explicar",
                {
                    "codigo": "x = 10",
                    "tipo": "token",
                    "tokenIndex": 2,
                    "pergunta": "Explique este token.",
                },
            )

        self.assertEqual(status, 200)
        self.assertEqual(data["explicacao"], "10 é um literal inteiro.")
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://ollama:11434/api/chat")
        body = json.loads(request.data.decode("utf-8"))
        prompt = json.loads(body["messages"][1]["content"])
        self.assertEqual(prompt["contexto"]["tokenSelecionado"]["lexema"], "10")

    def test_ai_endpoint_resolves_selected_ast_node_from_parser_output(self):
        ollama_response = io.BytesIO(
            json.dumps({"message": {"content": "O nó representa o valor."}}).encode("utf-8")
        )
        with patch("server.urlopen", return_value=ollama_response):
            status, data = self.request(
                "POST",
                "/api/ia/explicar",
                {
                    "codigo": "x = 10",
                    "tipo": "ast",
                    "caminhoNo": [0, 0],
                    "pergunta": "Explique o nó.",
                },
            )
        self.assertEqual(status, 200)
        self.assertEqual(data["explicacao"], "O nó representa o valor.")

    def test_ai_endpoint_handles_unavailable_ollama_and_invalid_kind(self):
        with patch("server.urlopen", side_effect=URLError("connection refused")):
            status, data = self.request(
                "POST",
                "/api/ia/explicar",
                {"codigo": "x = 10", "tipo": "pergunta", "pergunta": "Explique."},
            )
        self.assertEqual(status, 503)
        self.assertIn("análise léxica e sintática continua funcionando", data["mensagem"])

        status, data = self.request(
            "POST",
            "/api/ia/explicar",
            {"codigo": "x = 10", "tipo": [], "pergunta": "Explique."},
        )
        self.assertEqual(status, 400)
        self.assertIn("tipo", data["mensagem"])

    def test_ai_endpoint_reports_timeout_and_invalid_model_response(self):
        body = {"codigo": "x = 10", "tipo": "pergunta", "pergunta": "Explique."}
        with patch("server.urlopen", side_effect=TimeoutError()):
            timeout_status, timeout_data = self.request("POST", "/api/ia/explicar", body)
        self.assertEqual(timeout_status, 504)
        self.assertIn("demorou demais", timeout_data["mensagem"])

        with patch("server.urlopen", return_value=io.BytesIO(b"not-json")):
            response_status, response_data = self.request("POST", "/api/ia/explicar", body)
        self.assertEqual(response_status, 502)
        self.assertIn("resposta inválida", response_data["mensagem"])

    def test_ai_endpoint_rejects_invalid_service_url(self):
        body = {"codigo": "x = 10", "tipo": "pergunta", "pergunta": "Explique."}
        with patch.dict(os.environ, {"OLLAMA_BASE_URL": "not-a-url"}):
            status, data = self.request("POST", "/api/ia/explicar", body)
        self.assertEqual(status, 503)
        self.assertIn("URL configurada", data["mensagem"])

    def test_analyze_rejects_empty_or_missing_source(self):
        for body in ({"codigo": "   "}, {}, {"codigo": 10}):
            with self.subTest(body=body):
                status, data = self.request("POST", "/api/analyze", body)
                self.assertEqual(status, 400)
                self.assertIn("mensagem", data)

    def test_analyze_rejects_malformed_json(self):
        connection = HTTPConnection(self.host, self.port)
        connection.request(
            "POST",
            "/api/analyze",
            b'{"codigo":',
            {"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        data = json.loads(response.read())
        connection.close()
        self.assertEqual(response.status, 400)
        self.assertEqual(data["mensagem"], "Envie um JSON válido.")

    def test_unknown_route_returns_not_found(self):
        status, data = self.request("POST", "/api/unknown", {"codigo": "x = 1"})
        self.assertEqual(status, 404)
        self.assertEqual(data["mensagem"], "Rota não encontrada.")


if __name__ == "__main__":
    unittest.main()
