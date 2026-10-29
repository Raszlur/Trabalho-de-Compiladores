# Compilador Educacional

Projeto educacional para visualizar e compreender as etapas de um compilador.

## Objetivo e escopo

- **Linguagem escolhida para análise:** Python.
- **Subconjunto inicial planejado:** atribuições simples, valores numéricos e textuais, operadores aritméticos (`+`, `-`, `*`, `/`) e estruturas condicionais (`if`/`else`).
- **Motivo da escolha:** Python tem sintaxe legível e é uma linguagem adequada para demonstrar conceitos de análise léxica, sintática e semântica sem começar com uma gramática excessivamente grande.

Nesta terceira etapa, a aplicação oferece um scanner léxico para o subconjunto documentado, integrado ao backend e à interface. A análise sintática e a análise semântica ainda serão implementadas nas próximas etapas.

## Estrutura do projeto

```text
.
├── backend/
│   ├── Dockerfile
│   ├── server.py
│   └── scanner.py
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── app.js
│       └── index.html
├── docker-compose.yml
├── tests/
│   ├── test_frontend.py
│   ├── test_scanner.py
│   └── test_server.py
├── .dockerignore
├── .gitignore
└── README.md
```

## Pré-requisitos

- Docker Engine 24 ou superior.
- Docker Compose v2 (comando `docker compose`).
- Git, caso o projeto seja clonado do GitHub.

Não é necessário instalar Python ou Node.js na máquina para executar a aplicação, pois os serviços são executados em contêineres.

## Inicialização

Na raiz do projeto, execute:

```bash
docker compose up --build
```

Depois, abra <http://localhost:8080> no navegador para inserir código e visualizar tokens e erros léxicos.

Para iniciar em segundo plano:

```bash
docker compose up --build -d
```

Para acompanhar os logs:

```bash
docker compose logs -f
```

## Encerramento

Para parar e remover os contêineres e a rede criada pelo Compose:

```bash
docker compose down
```

## Validação de instalação limpa

A validação deve ser feita em uma máquina ou diretório sem dependências do projeto:

1. Clone o repositório.
2. Entre na pasta clonada.
3. Execute `docker compose up --build`.
4. Acesse <http://localhost:8080>.
5. Insira um código, solicite a análise e confirme a tabela de tokens.
6. Execute `docker compose down`.

O frontend chama `GET /api/hello` por meio do proxy do Nginx. Assim, a mensagem só é marcada como conectada quando frontend e backend estão funcionando juntos.

## Escopo léxico do Python educacional

O scanner foi implementado em Python, sem dependências externas, para manter o ambiente Docker simples e tornar o algoritmo caractere a caractere fácil de estudar.

| Categoria | Subconjunto suportado | Exemplos |
|---|---|---|
| Palavras reservadas | `if`, `else`, `while`, `for`, `in`, `return`, `and`, `or`, `not`, `True`, `False`, `None` | `if`, `return` |
| Identificadores | letra ou `_`, seguidos de letras, dígitos ou `_` | `numero`, `_total2` |
| Literais inteiros | uma ou mais casas decimais | `0`, `42` |
| Literais reais | dígitos, ponto e dígitos | `3.14` |
| Literais de texto | texto entre aspas simples ou duplas; escapes são preservados | `'Ada'`, `"ok"` |
| Operadores | aritméticos, atribuição, comparação e atribuição composta | `+`, `-`, `*`, `/`, `%`, `=`, `==`, `!=`, `<=`, `>=`, `//`, `**`, `+=` |
| Delimitadores | agrupamento, separação, bloco e acesso | `(`, `)`, `[`, `]`, `{`, `}`, `,`, `;`, `:`, `.` |
| Comentários | comentário de linha iniciado por `#` | `# explicação` |
| Espaços | espaços, tabulações, quebras de linha e `\r` são ignorados | — |
| Caracteres não reconhecidos | geram `ERRO_LEXICO`, com lexema, linha, coluna e mensagem | `@`, `$` |

Um identificador iniciado por dígito, uma string sem fechamento, um número malformado ou um caractere fora do escopo gera erro, mas o scanner continua processando o restante. Não há comentários de bloco nem token separado para caractere: aspas simples e duplas são tratados como `LITERAL_STRING`.

## Funcionalidades da segunda etapa

### Interface e exemplos

A tela identifica o **Compilador Educacional** e a linguagem Python, possui um editor de código e uma área de resultados. O seletor de exemplos preenche o editor e o conteúdo continua editável:

1. **Variável e valor:** atribuições de texto e número.
2. **Operação aritmética:** atribuições e multiplicação.
3. **Estrutura condicional:** `if`/`else`, comparação e atribuição dentro de blocos.

O botão **Enviar para análise** valida o conteúdo no navegador e envia o código para o backend, que executa o scanner. O programa não é executado e a estrutura sintática ainda não é validada.

### Contrato da API

O frontend envia:

```http
POST /api/analyze
Content-Type: application/json
```

```json
{"codigo": "numero = 10"}
```

Em uma entrada válida, o backend responde HTTP `200`:

```json
{
  "mensagem": "Análise léxica concluída com sucesso.",
  "recebido": true,
  "caracteres": 11,
  "linhas": 1,
  "sucesso": true,
  "tokens": [
    {"tipo": "IDENTIFICADOR", "lexema": "numero", "linha": 1, "coluna": 1},
    {"tipo": "OPERADOR", "lexema": "=", "linha": 1, "coluna": 8},
    {"tipo": "LITERAL_INTEIRO", "lexema": "10", "linha": 1, "coluna": 10}
  ],
  "erros": []
}
```

Quando existem erros léxicos, a resposta continua sendo HTTP `200`, com `"sucesso": false`, os tokens reconhecidos e a lista `erros`. Entradas vazias, JSON inválido ou campo `codigo` ausente/não textual resultam em HTTP `400`. Códigos acima de 100.000 caracteres resultam em HTTP `413`. Falhas de comunicação são exibidas pelo frontend sem expor detalhes internos.

## Interface didática

A tela apresenta uma tabela com tipo, lexema, linha e coluna de cada token, além de uma lista de erros léxicos com localização. Também exibe a quantidade de tokens e uma explicação breve sobre a diferença entre token e lexema. Os três exemplos continuam editáveis antes do envio.

## Testes automatizados

Os testes usam apenas a biblioteca padrão do Python e cobrem o scanner (palavras reservadas, identificadores, literais, operadores, delimitadores, comentários, posições e erros), os endpoints, entradas inválidas, rota inexistente e o contrato dos controles da interface.

Na raiz do projeto, execute:

```bash
python -m unittest discover -s tests -v
```

Resultado da validação desta etapa: **13 testes aprovados** (suíte automatizada). O fluxo manual recomendado com Docker é abrir a tela, selecionar um exemplo, editar o editor, enviar e conferir a tabela de tokens; depois enviar um caractere como `@` e conferir a mensagem de erro.

Também foi validada a configuração do ambiente com:

```bash
docker compose config
```

## Evidências de validação

Com os contêineres em execução, o fluxo foi verificado em `http://localhost:8080`:

1. A interface carregou com o título **Compilador Educacional | Python**.
2. O exemplo **Estrutura condicional** foi selecionado e carregado no editor.
3. O botão **Enviar para análise** enviou o código para `POST /api/analyze`.
4. A interface exibiu a tabela de tokens, a quantidade de linhas e de caracteres recebidos.
5. O status informou que frontend e backend estavam conectados.

## Limitações conhecidas

- O scanner não valida a estrutura do programa: isso será responsabilidade do parser da Etapa 4.
- O subconjunto não inclui comentários de bloco, indentação como token, números científicos ou prefixos de strings.
- A execução dos contêineres depende de Docker Engine e Docker Compose instalados.

## Publicação no GitHub

Crie um repositório no GitHub, adicione a origem e envie o projeto:

```bash
git init
git add .
git commit -m "feat: cria estrutura inicial do compilador educacional"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git
git push -u origin main
```

Depois, compartilhe a URL do repositório com o professor (`rocha3runo`) conforme as orientações da disciplina.
