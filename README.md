# Compilador Educacional

Projeto educacional para visualizar e compreender as etapas de um compilador.

## Escopo da primeira etapa

- **Linguagem escolhida para análise:** Python.
- **Subconjunto inicial planejado:** declarações simples de variáveis, valores numéricos e textuais, operadores aritméticos (`+`, `-`, `*`, `/`) e estruturas condicionais (`if`/`else`).
- **Motivo da escolha:** Python tem sintaxe legível e é uma linguagem adequada para demonstrar conceitos de análise léxica, sintática e semântica sem começar com uma gramática excessivamente grande.

Nesta etapa, o analisador ainda não foi implementado. A aplicação comprova a estrutura de frontend, backend e comunicação entre os serviços para receber as próximas fases.

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

