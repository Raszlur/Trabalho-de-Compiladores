const examples = {
  variable: "nome = 'Ada'\nidade = 10",
  arithmetic: "base = 10\naltura = 5\narea = base * altura",
  conditional: "numero = 10\nif numero > 0:\n    resultado = numero + 1\nelse:\n    resultado = 0",
};

const sourceCodeElement = document.querySelector("#source-code");
const exampleSelectElement = document.querySelector("#example-select");
const analyzeButtonElement = document.querySelector("#analyze-button");
const resultElement = document.querySelector("#result");
const resultMessageElement = document.querySelector("#result-message");
const resultDetailsElement = document.querySelector("#result-details");
const statusElement = document.querySelector("#status");

function showResult(message, type = "", details = "") {
  resultElement.className = `result ${type}`.trim();
  resultMessageElement.textContent = message;
  resultDetailsElement.textContent = details;
}

exampleSelectElement.addEventListener("change", () => {
  const example = examples[exampleSelectElement.value];
  if (example !== undefined) {
    sourceCodeElement.value = example;
    showResult("Exemplo carregado. Você pode editá-lo antes de enviar.");
  }
});

analyzeButtonElement.addEventListener("click", async () => {
  const codigo = sourceCodeElement.value;
  if (!codigo.trim()) {
    showResult("Informe um código-fonte antes de solicitar a análise.", "error");
    return;
  }

  analyzeButtonElement.disabled = true;
  statusElement.textContent = "Enviando código ao backend...";
  showResult("Processando...");
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codigo }),
    });
    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error("Resposta inválida do servidor");
    }
    if (!response.ok) {
      showResult(data.mensagem || "Não foi possível processar o código.", "error");
      statusElement.textContent = "O backend recusou a entrada.";
      return;
    }
    showResult(data.mensagem, "success", `${data.linhas} linha(s) e ${data.caracteres} caractere(s) recebidos.`);
    statusElement.textContent = "Frontend e backend estão conectados.";
  } catch {
    showResult("Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.", "error");
    statusElement.textContent = "Falha de comunicação com o backend.";
  } finally {
    analyzeButtonElement.disabled = false;
  }
});
