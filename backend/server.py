from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json

from scanner import scan

MAX_SOURCE_LENGTH = 100_000


class ApiHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/api/hello":
            self._send_json(404, {"mensagem": "Rota não encontrada."})
            return

        self._send_json(
            200,
            {"message": "Hello, World!", "service": "backend"},
        )

    def do_OPTIONS(self) -> None:
        if self.path != "/api/analyze":
            self._send_json(404, {"mensagem": "Rota não encontrada."})
            return

        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self) -> None:
        if self.path != "/api/analyze":
            self._send_json(404, {"mensagem": "Rota não encontrada."})
            return

        content_length_header = self.headers.get("Content-Length")
        try:
            content_length = int(content_length_header or "0")
        except ValueError:
            self._send_json(400, {"mensagem": "O tamanho da requisição é inválido."})
            return

        if content_length > MAX_SOURCE_LENGTH + 1000:
            self._send_json(413, {"mensagem": "O código-fonte excede o limite permitido."})
            return

        try:
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"mensagem": "Envie um JSON válido."})
            return

        if not isinstance(data, dict) or not isinstance(data.get("codigo"), str):
            self._send_json(
                400,
                {"mensagem": 'O campo "codigo" deve ser informado como texto.'},
            )
            return

        codigo = data["codigo"]
        if not codigo.strip():
            self._send_json(
                400,
                {"mensagem": "Informe um código-fonte antes de solicitar a análise."},
            )
            return

        if len(codigo) > MAX_SOURCE_LENGTH:
            self._send_json(413, {"mensagem": "O código-fonte excede o limite permitido."})
            return

        tokens, erros = scan(codigo)
        self._send_json(
            200,
            {
                "mensagem": (
                    "Análise léxica concluída com sucesso."
                    if not erros
                    else "Análise léxica concluída com erros. Consulte os detalhes."
                ),
                "recebido": True,
                "caracteres": len(codigo),
                "linhas": len(codigo.splitlines()) or 1,
                "sucesso": not erros,
                "tokens": tokens,
                "erros": erros,
            },
        )

    def _send_json(self, status: int, response: dict[str, object]) -> None:
        payload = json.dumps(response, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), ApiHandler)
    print("Backend disponível na porta 8000")
    server.serve_forever()
