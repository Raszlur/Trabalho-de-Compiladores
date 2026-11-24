# Registro de validação — Etapa 4

## Testes executados

Data do registro: 24/11/2026.

| Verificação | Comando/ação | Resultado |
|---|---|---|
| Testes automatizados | `python -m unittest discover -s tests -v` | **28 testes aprovados**, incluindo regressão do scanner, parser, API, interface e falhas/respostas simuladas do Ollama. |
| Sintaxe e diagnósticos Python | Pylance em `backend/parser.py` e `backend/server.py` | Nenhum erro de sintaxe ou diagnóstico nesses dois módulos. |
| Compose padrão | `docker compose config` | Configuração validada. |
| Perfil opcional de IA | `docker compose --profile ai config` | Configuração, serviço `ollama` e volume `ollama_data` validados. |
| Serviço em contêiner | `docker compose up --build -d` | Imagens construídas e `frontend`/`backend` iniciados; ambos reportados como `Up`. |
| Fluxo HTTP e análise | `http://localhost:8080`, `POST /api/analyze` | Frontend HTTP `200`; programa válido retornou 7 tokens e AST `PROGRAMA` com `MULTIPLICACAO` abaixo de `SOMA`; sintaxe inválida retornou diagnóstico; erro léxico preservou tokens e marcou parser como não executado. |
| Interface no navegador | Análise do exemplo aritmético e erro | Árvore exibida e expandir/recolher funcionou; seleção de `MULTIPLICACAO` destacou `5 * 2` no editor. Entrada com erro léxico/sintático exibiu mensagens sem erro JavaScript. |
| IA indisponível | Solicitação na interface sem contêiner Ollama | Endpoint retornou `503` amigável; a análise do compilador continuou funcionando. |
| Modelo real do Ollama | `docker compose --profile ai exec ollama ollama pull llama3.2` | Pendente: não foi baixado. A suíte automatizada usa respostas simuladas e não comprova inferência real. |

O fluxo do compilador nos contêineres foi validado. Não se declara validada a inferência real do Llama 3.2; o modelo ainda não foi baixado nem testado.

## Demonstração reproduzível da API de IA

Com o perfil `ai` iniciado e o modelo baixado, o nó `MULTIPLICACAO` no código `resultado = 10 + 5 * 2` pode ser solicitado por:

```powershell
$body = @{
  codigo = "resultado = 10 + 5 * 2"
  tipo = "ast"
  caminhoNo = @(0, 0, 1)
  pergunta = "Por que a multiplicação aparece abaixo da soma nesta AST?"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
  -Uri "http://localhost:8080/api/ia/explicar" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

O caminho é calculado na AST real: `PROGRAMA` → `ATRIBUICAO` → `SOMA` → segundo filho (`MULTIPLICACAO`). O backend não aceita a AST do cliente como fonte de verdade; ele refaz as análises e resolve o caminho na saída do parser.

Formato de resposta do endpoint:

```json
{
  "explicacao": "<texto retornado pelo modelo>",
  "geradaPor": "llama3.2",
  "aviso": "A explicação é gerada por IA; tokens, AST e diagnósticos oficiais vêm do compilador."
}
```

Exemplo **ilustrativo, não capturado de uma execução do modelo**:

> A multiplicação aparece como filha da soma porque a gramática dá maior precedência a `*` do que a `+`. Assim, o parser agrupa primeiro `5 * 2` e depois soma esse resultado a `10`. Esse agrupamento é refletido na AST.

Para validar a resposta real, execute os comandos da seção Ollama no README, use a interface ou envie a requisição acima, e registre a resposta efetivamente obtida.

## Verificações manuais após iniciar o Compose

1. Execute `docker compose up --build` e confirme que `frontend` e `backend` estão ativos.
2. Abra <http://localhost:8080> e analise `resultado = 10 + 5 * 2`.
3. Confirme os sete tokens e que a AST organiza `MULTIPLICACAO` abaixo de `SOMA`.
4. Selecione um nó; confirme o realce do intervalo no editor e a disponibilidade da explicação contextual.
5. Analise `if numero > 0` sem `:` e confirme o erro sintático com posição.
6. Analise `resultado = @` e confirme que os erros léxicos aparecem e o parser é explicitamente ignorado.
7. Teste o perfil normal sem Ollama e confirme que scanner/parser seguem funcionais.
8. Inicie o perfil `ai`, baixe `llama3.2`, solicite a explicação e confira que a interface identifica o texto como gerado por IA.
9. Encerre com `docker compose down`.

Registre resultados e eventuais correções neste arquivo após realizar os passos. Não marque etapas pendentes como aprovadas sem executá-las.
