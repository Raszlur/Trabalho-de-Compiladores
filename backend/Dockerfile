FROM python:3.12-slim

WORKDIR /app

COPY server.py .
COPY scanner.py .
COPY parser.py .

EXPOSE 8000

CMD ["python", "server.py"]
