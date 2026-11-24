# Compilador Educacional

Aplicação didática que demonstra análise léxica e sintática de um subconjunto de Python. O scanner e o parser são implementados no backend; o frontend mostra tokens, diagnósticos e a Árvore Sintática Abstrata (AST).

## Escopo da Etapa 4

- **Linguagem de referência:** Python.
- **Estratégia do parser:** descendente recursivo, implementado manualmente em Python, sem dependências externas.
- **Construções analisadas:** atribuições simples, literais inteiros/reais/textuais/booleanos/nulos, expressões, operadores aritméticos, comparações, operadores lógicos, parênteses, blocos indentados e condicionais `if`/`else`.
- **Ainda não implementado:** análise semântica, tabela de símbolos, chamadas/funções, laços, listas, acesso a atributos/índices, `elif` e execução do programa.

O parser reutiliza o scanner da Etapa 3. Ele usa as linhas e colunas já associadas aos tokens para reconhecer limites de instruções e níveis de indentação; o formato e as categorias dos tokens não foram alterados. Consulte a [gramática formal](docs/gramatica.md) para as produções e limitações completas.

## Estrutura

```text
.
├── backend/
│   ├── Dockerfile
│   ├── parser.py
│   ├── scanner.py
│   └── server.py
├── docs/
│   ├── fluxograma.md
│   ├── gramatica.md
│   └── validacao-etapa4.md
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
├── tests/
│   ├── test_frontend.py
│   ├── test_parser.py
│   ├── test_scanner.py
│   └── test_server.py
└── docker-compose.yml
```

## Requisitos

- Docker Engine e Docker Compose v2 (`docker compose`).
- Python 3.10+ para executar os testes fora dos contêineres.
- Ollama e o modelo Llama 3.2 são opcionais; a aplicação principal não depende deles.

## Executar a aplicação principal

Na raiz do repositório:

```bash
docker compose up --build
```

Abra <http://localhost:8080>, escolha um exemplo ou escreva código e clique em **Enviar para análise**. A tela apresenta tokens, erros léxicos/sintáticos e a AST. Ao terminar:

```bash
docker compose down
```

O serviço normal não inicia nem baixa o Ollama.

## Análise sintática e AST

Exemplo válido:

```python
resultado = 10 + 5 * 2
```

A AST coloca `MULTIPLICACAO` como filha de `SOMA`, porque `*` tem precedência maior que `+`. O frontend permite expandir/recolher a árvore, destacar no editor o intervalo de um nó, solicitar explicação contextual à IA e baixar a AST como JSON.

Uma resposta sintática bem-sucedida inclui o contrato anterior da Etapa 3 e os novos resultados:

```json
{
  "mensagem": "Análise léxica concluída com sucesso.",
  "recebido": true,
  "caracteres": 5,
  "linhas": 1,
  "sucesso": true,
  "tokens": [
    {"tipo": "IDENTIFICADOR", "lexema": "x", "linha": 1, "coluna": 1},
    {"tipo": "OPERADOR", "lexema": "=", "linha": 1, "coluna": 3},
    {"tipo": "LITERAL_INTEIRO", "lexema": "1", "linha": 1, "coluna": 5}
  ],
  "erros": [],
  "lexico": {
    "sucesso": true,
    "tokens": [
      {"tipo": "IDENTIFICADOR", "lexema": "x", "linha": 1, "coluna": 1},
      {"tipo": "OPERADOR", "lexema": "=", "linha": 1, "coluna": 3},
      {"tipo": "LITERAL_INTEIRO", "lexema": "1", "linha": 1, "coluna": 5}
    ],
    "erros": []
  },
  "sintatico": {
    "executado": true,
    "sucesso": true,
    "ast": {
      "tipo": "PROGRAMA",
      "linha": 1,
      "coluna": 1,
      "linhaFim": 1,
      "colunaFim": 5,
      "atributos": {},
      "filhos": [
        {
          "tipo": "ATRIBUICAO",
          "linha": 1,
          "coluna": 1,
          "linhaFim": 1,
          "colunaFim": 5,
          "atributos": {"nome": "x", "operador": "="},
          "filhos": [
            {
              "tipo": "LITERAL_INTEIRO",
              "linha": 1,
              "coluna": 5,
              "linhaFim": 1,
              "colunaFim": 5,
              "atributos": {"valor": "1"},
              "filhos": [],
              "regra": "primaria ::= LITERAL"
            }
          ],
          "regra": "atribuicao ::= IDENTIFICADOR '=' expressao"
        }
      ],
      "regra": "programa ::= { comando }"
    },
    "erros": [],
    "mensagem": "Análise sintática concluída com sucesso."
  }
}
```
O exemplo corresponde à requisição `{"codigo": "x = 1"}`.

Os campos legados `recebido`, `caracteres`, `linhas`, `sucesso`, `tokens` e `erros` são preservados. `sucesso` e `erros` no nível superior continuam descrevendo a análise léxica, para compatibilidade com a Etapa 3; o resultado sintático fica em `sintatico`.

Quando há erro sintático, `sintatico.sucesso` é `false`, `sintatico.ast` é `null` e `sintatico.erros` informa tipo, linha, coluna, token encontrado, itens esperados e mensagem didática. O parser reporta o primeiro erro, conforme permitido no enunciado; não tenta sincronização nem acumula erros em cascata.

Se o scanner encontrar erros léxicos, o parser não é executado. Os tokens reconhecidos e todos os erros léxicos continuam sendo apresentados; `sintatico.executado` será `false` e a AST será `null`.

## API

### `POST /api/analyze`

Requisição:

```json
{"codigo": "resultado = 10 + 5 * 2"}
```

Responde HTTP `200` com campos legados da Etapa 3 e os objetos `lexico` e `sintatico`. JSON inválido, texto vazio e campo ausente/não textual resultam em `400`; código com mais de 100.000 caracteres resulta em `413`. Erros de análise são diagnósticos no corpo da resposta e não falhas HTTP.

### `POST /api/ia/explicar` (opcional)

O frontend solicita explicações contextuais para um token ou nó real da AST, ou envia uma pergunta conceitual. Exemplos de campos adicionais:

```json
{
  "tipo": "ast",
  "pergunta": "Por que este nó aparece abaixo da soma?",
  "caminhoNo": [0, 0]
}
```

Tipos aceitos: `token` (com `tokenIndex`), `ast` (com `caminhoNo`) ou `pergunta`. O backend sempre executa novamente o scanner/parser e deriva os dados selecionados dos resultados reais; não confia em AST/tokens enviados pelo navegador. O acesso ao Ollama ocorre exclusivamente no backend. Limites: código de até 20.000 caracteres para explicações, pergunta de até 2.000 caracteres e timeout de 60 segundos. Indisponibilidade da IA retorna uma resposta de erro clara sem afetar a análise do compilador.

## Ollama e Llama 3.2 (diferencial opcional)

O serviço usa o modelo `llama3.2` via API `POST /api/chat`. Ele está no perfil Compose `ai`, não publica a porta do Ollama no host e persiste os modelos no volume `ollama_data`.

```bash
docker compose --profile ai up --build -d
docker compose exec ollama ollama pull llama3.2
docker compose exec ollama ollama list
```

Abra a aplicação em <http://localhost:8080>. Analise um exemplo e use **Explicar token**, **Selecionar nó e explicar com IA** ou a caixa **Pergunte sobre a análise**. O frontend indica que a explicação foi gerada por IA. Para parar os serviços:

```bash
docker compose down
```

Configuração do backend: `OLLAMA_BASE_URL` (padrão `http://ollama:11434`) e `OLLAMA_MODEL` (padrão `llama3.2`). Para uma demonstração de API, formato enviado e exemplo de resposta ilustrativa, veja [validação e demonstração](docs/validacao-etapa4.md). A resposta do modelo é apoio didático, não resultado oficial do compilador.

## Testes

Na raiz do projeto:

```bash
python -m unittest discover -s tests -v
```

Os testes cobrem scanner/regressão, parser, precedência/associatividade, blocos aninhados, localizações e erros, endpoints e o contrato de interface. A integração Ollama é testada com resposta simulada para não exigir baixar o modelo na suíte automatizada. Consulte [registro de validação](docs/validacao-etapa4.md).

## Próximas etapas

A análise semântica — como resolução de identificadores e compatibilidade de tipos — ainda não foi implementada e é parte da Etapa 5. Decisões do fluxo para o artigo estão em [fluxograma e notas metodológicas](docs/fluxograma.md). A pesquisa bibliográfica e a comparação com ferramentas devem ser concluídas com as fontes acadêmicas efetivamente consultadas; não se afirma novidade ou exclusividade sem evidência.

## Repositório

O projeto está publicado em [Raszlur/Trabalho-de-Compiladores](https://github.com/Raszlur/Trabalho-de-Compiladores). Compartilhe esse endereço com o professor `rocha3runo` conforme as orientações da disciplina.
