# Gramática do subconjunto analisado

O parser reconhece um subconjunto didático de Python. A notação abaixo é EBNF; `ε` significa vazio, `{ X }` repetição (zero ou mais) e `[ X ]` opcional.

## Símbolo inicial, terminais e não terminais

- **Símbolo inicial:** `programa`.
- **Não terminais:** `programa`, `comando`, `bloco`, `linha_simples`, `atribuicao`, `condicional`, `expressao`, `disjuncao`, `conjuncao`, `negacao`, `comparacao`, `soma`, `produto`, `unaria`, `potencia`, `primaria`.
- **Terminais:** palavras-chave `if`, `else`, `and`, `or`, `not`, `True`, `False`, `None`; tokens `IDENTIFICADOR`, `LITERAL_INTEIRO`, `LITERAL_REAL`, `LITERAL_STRING`; operadores `=`, `+`, `-`, `*`, `/`, `//`, `%`, `**`, `==`, `!=`, `<`, `<=`, `>`, `>=`; delimitadores `:`, `;`, `(` e `)`.

## Produções

```ebnf
programa       = { comando } ;
comando        = condicional | linha_simples ;

linha_simples  = atribuicao, { ";", atribuicao }, [ ";" ] ;
atribuicao     = IDENTIFICADOR, "=", expressao ;

condicional    = "if", expressao, ":", bloco, [ "else", ":", bloco ] ;
bloco          = NOVA_LINHA, INDENT, comando, { comando }, DEDENT ;

expressao      = disjuncao ;
disjuncao      = conjuncao, { "or", conjuncao } ;
conjuncao      = negacao, { "and", negacao } ;
negacao        = "not", negacao | comparacao ;
comparacao     = soma, [ operador_comparacao, soma ] ;
operador_comparacao = "==" | "!=" | "<" | "<=" | ">" | ">=" ;
soma           = produto, { ("+" | "-"), produto } ;
produto        = unaria, { ("*" | "/" | "//" | "%"), unaria } ;
unaria         = ("+" | "-"), unaria | potencia ;
potencia       = primaria, [ "**", unaria ] ;
primaria       = IDENTIFICADOR
               | LITERAL_INTEIRO
               | LITERAL_REAL
               | LITERAL_STRING
               | "True"
               | "False"
               | "None"
               | "(", expressao, ")" ;
```

O parser não exige tokens `NOVA_LINHA`, `INDENT` ou `DEDENT` novos. O scanner da Etapa 3 mantém sua saída; o parser usa `linha` e `coluna` dos tokens para identificar fim de linha e indentação. Uma instrução de nível principal começa na coluna 1. O primeiro comando do bloco estabelece sua coluna de indentação; os comandos irmãos devem manter essa coluna. Blocos vazios e comandos inline depois de `:` não são aceitos.

## Correspondência com o scanner

| Terminal da gramática | Saída do scanner |
|---|---|
| `IDENTIFICADOR` | `tipo: IDENTIFICADOR` |
| Inteiro/real/texto | `LITERAL_INTEIRO`, `LITERAL_REAL`, `LITERAL_STRING` |
| `if`, `else`, `and`, `or`, `not`, `True`, `False`, `None` | `PALAVRA_RESERVADA` e o lexema correspondente |
| Operadores aritméticos, comparação e `=` | `OPERADOR` e o lexema correspondente |
| `:`, `;`, `(`, `)` | `DELIMITADOR` e o lexema correspondente |
| Nova linha/indentação | Não são tokens; inferidos por posições dos tokens subsequentes |

O scanner aceita categorias adicionais, incluindo `while`, `for`, `in`, `return`, `[]`, `{}`, `.`, vírgulas e atribuições compostas. Reconhecê-las lexicalmente não significa que o parser as aceite: estão fora da gramática atual.

## Precedência e associatividade

Da maior para a menor precedência:

1. Parênteses;
2. Potência `**` (associativa à direita);
3. Unários `+` e `-` (a potência liga mais fortemente: `-2 ** 2` equivale estruturalmente a `-(2 ** 2)`);
4. `*`, `/`, `//`, `%` (associativos à esquerda);
5. `+`, `-` (associativos à esquerda);
6. Comparação (uma comparação por expressão; comparação encadeada não suportada);
7. `not`;
8. `and`;
9. `or`.

Exemplos: `2 + 3 * 4` produz `SOMA(2, MULTIPLICACAO(3, 4))`; `10 - 3 - 2` agrupa como `(10 - 3) - 2`; `(10 + 5) * 2` mantém a soma dentro de um nó `AGRUPAMENTO`.

## Construções dentro e fora do escopo

**Suportadas:** programa vazio/com comentários; atribuições de um nome; operadores da gramática; valores inteiros, reais, strings, booleanos e `None`; parênteses; `if` e `else` com blocos indentados; aninhamento de condicionais; atribuições separadas por `;` na mesma linha.

**Fora do escopo sintático:** declarações tipadas; chamadas e definições de função; `return`; `while`, `for`, `elif`, `in`; listas e dicionários; índices/atributos; operadores de atribuição composta; comparações encadeadas; strings multilinha; indentação implícita dentro de parênteses; execução e análise semântica. O parser retorna o primeiro erro sintático e não faz recuperação/sincronização.

## AST e exemplos

Cada nó serializado tem o formato:

```json
{
  "tipo": "ATRIBUICAO",
  "linha": 1,
  "coluna": 1,
  "linhaFim": 1,
  "colunaFim": 25,
  "atributos": {"nome": "resultado", "operador": "="},
  "filhos": [],
  "regra": "atribuicao ::= IDENTIFICADOR '=' expressao"
}
```

Todos os nós seguem o mesmo formato. `linha`/`coluna` e `linhaFim`/`colunaFim` são posições inclusivas do trecho associado; nós de expressão referenciam os operandos e nós de bloco contêm os comandos. `PROGRAMA`, `ATRIBUICAO`, `CONDICIONAL`, `BLOCO`, `AGRUPAMENTO`, `IDENTIFICADOR`, nós de literais e operadores são tipos usados na implementação.

Para:

```python
resultado = 10 + 5 * 2
```

a forma estrutural relevante é:

```text
PROGRAMA
└── ATRIBUICAO(nome=resultado)
    └── SOMA
        ├── LITERAL_INTEIRO(valor=10)
        └── MULTIPLICACAO
            ├── LITERAL_INTEIRO(valor=5)
            └── LITERAL_INTEIRO(valor=2)
```

Isto é uma **AST**, não uma árvore de derivação completa: terminais auxiliares como `=` e parênteses não são nós próprios (o agrupamento explícito recebe nó `AGRUPAMENTO`).

Exemplos inválidos:

```python
if numero > 0
    resultado = 1
```

Erro esperado: falta `:` após a condição, indicando posição e token encontrado.

```python
resultado = 10 +
```

Erro esperado: fim do código antes do operando; a AST é `null`.
