import json
import pathlib
import sys
import threading
import unittest
from http.client import HTTPConnection

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "backend"))
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
        self.assertEqual(data["linhas"], 1)
        self.assertEqual(data["caracteres"], 7)

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
