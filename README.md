# Compilador Educacional

Projeto educacional para visualizar e compreender as etapas de um compilador.

## Objetivo e escopo

- **Linguagem escolhida para análise:** Python.
- **Subconjunto inicial planejado:** atribuições simples, valores numéricos e textuais, operadores aritméticos (`+`, `-`, `*`, `/`) e estruturas condicionais (`if`/`else`).
- **Motivo da escolha:** Python tem sintaxe legível e é uma linguagem adequada para demonstrar conceitos de análise léxica, sintática e semântica sem começar com uma gramática excessivamente grande.

Nesta segunda etapa, a aplicação oferece a entrada de código, exemplos selecionáveis, validações e comunicação real entre frontend e backend. A análise léxica, sintática e semântica ainda será implementada nas próximas etapas.

## Estrutura do projeto

```text
.
├── backend/
│   ├── Dockerfile
│   └── server.py
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── app.js
│       └── index.html
├── docker-compose.yml
├── tests/
│   ├── test_frontend.py
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

Depois, abra <http://localhost:8080> no navegador. A interface exibirá **Hello, World!** após consultar o backend.

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
5. Confirme a mensagem **Hello, World!** e o indicador de backend conectado.
6. Execute `docker compose down`.

O frontend chama `GET /api/hello` por meio do proxy do Nginx. Assim, a mensagem só é marcada como conectada quando frontend e backend estão funcionando juntos.

## Funcionalidades da segunda etapa

### Interface e exemplos

A tela identifica o **Compilador Educacional** e a linguagem Python, possui um editor de código e uma área de resultados. O seletor de exemplos preenche o editor e o conteúdo continua editável:

1. **Variável e valor:** atribuições de texto e número.
2. **Operação aritmética:** atribuições e multiplicação.
3. **Estrutura condicional:** `if`/`else`, comparação e atribuição dentro de blocos.

O botão **Enviar para análise** valida o conteúdo no navegador e envia o código para o backend. Nesta etapa, enviar não executa o programa nem substitui os analisadores que serão desenvolvidos depois.

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
  "mensagem": "Código recebido com sucesso. A análise será adicionada nas próximas etapas.",
  "recebido": true,
  "caracteres": 11,
  "linhas": 1
}
```

Entradas vazias, JSON inválido ou campo `codigo` ausente/não textual resultam em HTTP `400`. Códigos acima de 100.000 caracteres resultam em HTTP `413`. Falhas de comunicação são exibidas pelo frontend sem expor detalhes internos.

## Testes automatizados

Os testes usam apenas a biblioteca padrão do Python e cobrem o endpoint legado, o envio válido, entradas inválidas, rota inexistente e o contrato dos controles da interface.

Na raiz do projeto, execute:

```bash
python -m unittest discover -s tests -v
```

Resultado da validação desta etapa: **8 testes aprovados**. A verificação automatizada do frontend cobre o contrato dos arquivos HTML/JavaScript. Além disso, foi realizado um fluxo manual no navegador com Docker: abertura da tela, seleção do exemplo condicional, preenchimento do editor, envio e apresentação da resposta do backend.

Também foi validada a configuração do ambiente com:

```bash
docker compose config
```

## Evidências de validação

Com os contêineres em execução, o fluxo foi verificado em `http://localhost:8080`:

1. A interface carregou com o título **Compilador Educacional | Python**.
2. O exemplo **Estrutura condicional** foi selecionado e carregado no editor.
3. O botão **Enviar para análise** enviou o código para `POST /api/analyze`.
4. A interface exibiu a confirmação, a quantidade de linhas e de caracteres recebidos.
5. O status informou que frontend e backend estavam conectados.

## Limitações conhecidas

- O backend apenas valida e registra o recebimento do texto; ainda não há tokenização, parser ou análise semântica.
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
