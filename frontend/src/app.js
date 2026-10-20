const messageElement = document.querySelector("#message");
const statusElement = document.querySelector("#status");

fetch("/api/hello")
  .then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  })
  .then((data) => {
    messageElement.textContent = data.message;
    statusElement.textContent = "Frontend e backend estão conectados.";
  })
  .catch((error) => {
    messageElement.textContent = "Não foi possível carregar a mensagem";
    statusElement.textContent = `Erro de comunicação com o backend: ${error.message}`;
  });

