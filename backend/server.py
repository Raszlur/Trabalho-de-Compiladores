from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json


class ApiHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/api/hello":
            self.send_error(404, "Rota não encontrada")
            return

        payload = json.dumps(
            {"message": "Hello, World!", "service": "backend"},
            ensure_ascii=False,
        ).encode("utf-8")
        self.send_response(200)
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

