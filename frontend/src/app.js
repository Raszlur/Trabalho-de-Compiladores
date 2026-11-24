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
const tokenCountElement = document.querySelector("#token-count");
const tokenTableBodyElement = document.querySelector("#token-table-body");
const lexicalErrorsElement = document.querySelector("#lexical-errors");
const syntaxStatusElement = document.querySelector("#syntax-status");
const syntaxErrorsElement = document.querySelector("#syntax-errors");
const astTreeElement = document.querySelector("#ast-tree");
const aiQuestionElement = document.querySelector("#ai-question");
const aiQuestionButtonElement = document.querySelector("#ai-question-button");
const aiStatusElement = document.querySelector("#ai-status");
const aiResponseElement = document.querySelector("#ai-response");
const downloadAstButtonElement = document.querySelector("#download-ast");

let lastAnalyzedCode = "";
let lastAst = null;

function showResult(message, type = "", details = "") {
  resultElement.className = `result ${type}`.trim();
  resultMessageElement.textContent = message;
  resultDetailsElement.textContent = details;
}

function renderLexicalErrors(errors) {
  lexicalErrorsElement.replaceChildren();
  errors.forEach((error) => {
    const item = document.createElement("li");
    item.textContent = `Linha ${error.linha}, coluna ${error.coluna}: ${error.mensagem}`;
    lexicalErrorsElement.append(item);
  });
}

function renderSyntaxErrors(errors) {
  syntaxErrorsElement.replaceChildren();
  errors.forEach((error) => {
    const item = document.createElement("li");
    item.textContent = `${error.mensagem} Esperado: ${error.esperado.join(", ")}.`;
    syntaxErrorsElement.append(item);
  });
}

function sourceOffset(line, column) {
  const lines = lastAnalyzedCode.split("\n");
  let offset = 0;
  for (let index = 0; index < line - 1 && index < lines.length; index += 1) {
    offset += lines[index].length + 1;
  }
  return Math.min(offset + column - 1, lastAnalyzedCode.length);
}

function selectNodeSource(node) {
  const start = sourceOffset(node.linha, node.coluna);
  const end = sourceOffset(node.linhaFim, node.colunaFim + 1);
  sourceCodeElement.focus();
  sourceCodeElement.setSelectionRange(start, Math.max(start, end));
}

function describeNode(node) {
  const attributes = Object.entries(node.atributos || {})
    .map(([name, value]) => `${name}: ${value}`)
    .join(", ");
  return attributes ? `${node.tipo} (${attributes})` : node.tipo;
}

function renderAstNode(node, path = []) {
  const item = document.createElement("li");
  const details = document.createElement("details");
  details.open = true;
  const summary = document.createElement("summary");
  const label = document.createElement("span");
  label.className = "ast-node-label";
  label.textContent = `${describeNode(node)} — linha ${node.linha}, coluna ${node.coluna}`;
  summary.append(label);
  details.append(summary);

  const action = document.createElement("button");
  action.type = "button";
  action.className = "ast-node-action ai-action";
  action.textContent = "Selecionar nó e explicar com IA";
  action.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    selectNodeSource(node);
    explainWithAI({
      tipo: "ast",
      caminhoNo: path,
      pergunta: `Explique didaticamente o nó ${describeNode(node)}, a regra gramatical associada e sua relação com os nós ancestrais e filhos.`,
    });
  });
  details.append(action);

  if (node.filhos.length > 0) {
    const children = document.createElement("ul");
    node.filhos.forEach((child, index) => {
      children.append(renderAstNode(child, [...path, index]));
    });
    details.append(children);
  }
  item.append(details);
  return item;
}

function showAnalysis(data, codigo) {
  lastAnalyzedCode = codigo;
  lastAst = data.sintatico.ast;
  tokenCountElement.textContent = `${data.tokens.length} token(s) identificado(s).`;
  tokenTableBodyElement.replaceChildren();
  data.tokens.forEach((token, tokenIndex) => {
    const row = document.createElement("tr");
    [token.tipo, token.lexema, token.linha, token.coluna].forEach((value, index) => {
      const cell = document.createElement("td");
      if (index === 1) {
        const code = document.createElement("code");
        code.textContent = value;
        cell.append(code);
      } else {
        cell.textContent = value;
      }
      row.append(cell);
    });

    const actionCell = document.createElement("td");
    const action = document.createElement("button");
    action.type = "button";
    action.className = "token-action ai-action";
    action.textContent = "Explicar token";
    action.addEventListener("click", () => {
      explainWithAI({
        tipo: "token",
        tokenIndex,
        pergunta: `Explique o token ${token.tipo} com lexema ${JSON.stringify(token.lexema)}, incluindo sua função no código-fonte.`,
      });
    });
    actionCell.append(action);
    row.append(actionCell);
    tokenTableBodyElement.append(row);
  });

  renderLexicalErrors(data.erros);
  renderSyntaxErrors(data.sintatico.erros);
  syntaxStatusElement.textContent = data.sintatico.mensagem;
  astTreeElement.replaceChildren();
  if (data.sintatico.ast) {
    const tree = document.createElement("ul");
    tree.className = "ast-tree";
    tree.append(renderAstNode(data.sintatico.ast));
    astTreeElement.append(tree);
  } else {
    astTreeElement.textContent = data.sintatico.executado
      ? "A AST não foi construída porque o programa contém erros sintáticos."
      : "A AST não foi construída porque o scanner encontrou erros léxicos.";
  }
  downloadAstButtonElement.disabled = !lastAst;

  const successful = data.lexico.sucesso && data.sintatico.sucesso;
  const resultType = successful ? "success" : "error";
  showResult(
    successful ? "Análise léxica e sintática concluída com sucesso." : "A análise encontrou problemas.",
    resultType,
    `${data.linhas} linha(s), ${data.caracteres} caractere(s) e ${data.tokens.length} token(s).`,
  );
  if (!data.lexico.sucesso) {
    statusElement.textContent = "Parser não executado: corrija os erros léxicos indicados.";
  } else if (!data.sintatico.sucesso) {
    statusElement.textContent = "Scanner concluído; corrija os erros sintáticos indicados.";
  } else {
    statusElement.textContent = "Análise léxica e sintática concluída.";
  }
}

async function explainWithAI(requestData) {
  if (!lastAnalyzedCode) {
    aiStatusElement.textContent = "Execute primeiro a análise do código.";
    return;
  }
  const actionButtons = document.querySelectorAll(".ai-action");
  actionButtons.forEach((button) => {
    button.disabled = true;
  });
  aiQuestionButtonElement.disabled = true;
  aiStatusElement.textContent = "Consultando Ollama + Llama 3.2...";
  aiResponseElement.textContent = "A explicação está sendo gerada.";
  try {
    const response = await fetch("/api/ia/explicar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codigo: lastAnalyzedCode, ...requestData }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.mensagem || "O professor virtual não pôde responder.");
    }
    aiResponseElement.textContent = data.explicacao;
    aiStatusElement.textContent = `Explicação gerada por IA (${data.geradaPor}).`;
  } catch (error) {
    aiResponseElement.textContent = error.message || "Falha de comunicação com o serviço de IA.";
    aiStatusElement.textContent = "A IA não está disponível; a análise do compilador continua independente.";
  } finally {
    actionButtons.forEach((button) => {
      button.disabled = false;
    });
    aiQuestionButtonElement.disabled = false;
  }
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
  showResult("Processando análise léxica e sintática...");
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
    showAnalysis(data, codigo);
  } catch {
    showResult("Não foi possível comunicar com o servidor. Verifique a conexão e tente novamente.", "error");
    statusElement.textContent = "Falha de comunicação com o backend.";
  } finally {
    analyzeButtonElement.disabled = false;
  }
});

aiQuestionButtonElement.addEventListener("click", () => {
  const pergunta = aiQuestionElement.value.trim();
  if (!pergunta) {
    aiStatusElement.textContent = "Digite uma pergunta antes de consultar o professor virtual.";
    return;
  }
  explainWithAI({ tipo: "pergunta", pergunta });
});

document.querySelector("#expand-ast").addEventListener("click", () => {
  document.querySelectorAll("#ast-tree details").forEach((details) => {
    details.open = true;
  });
});

document.querySelector("#collapse-ast").addEventListener("click", () => {
  document.querySelectorAll("#ast-tree details").forEach((details) => {
    details.open = false;
  });
});

downloadAstButtonElement.addEventListener("click", () => {
  if (!lastAst) {
    return;
  }
  const file = new Blob([JSON.stringify(lastAst, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(file);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ast.json";
  link.click();
  URL.revokeObjectURL(url);
});
