"""Parser descendente recursivo para o subconjunto educacional de Python."""

from dataclasses import dataclass
from typing import NoReturn, Sequence

from scanner import Token


MAX_NESTING_DEPTH = 100


@dataclass
class Node:
    tipo: str
    linha: int
    coluna: int
    linha_fim: int
    coluna_fim: int
    atributos: dict[str, object]
    filhos: list["Node"]
    regra: str

    def as_dict(self) -> dict[str, object]:
        return {
            "tipo": self.tipo,
            "linha": self.linha,
            "coluna": self.coluna,
            "linhaFim": self.linha_fim,
            "colunaFim": self.coluna_fim,
            "atributos": self.atributos,
            "filhos": [child.as_dict() for child in self.filhos],
            "regra": self.regra,
        }


@dataclass
class SyntaxError:
    linha: int
    coluna: int
    encontrado: str
    esperado: list[str]
    mensagem: str

    def as_dict(self) -> dict[str, object]:
        return {
            "tipo": "ERRO_SINTATICO",
            "linha": self.linha,
            "coluna": self.coluna,
            "encontrado": self.encontrado,
            "esperado": self.esperado,
            "mensagem": self.mensagem,
        }


class ParseFailure(Exception):
    def __init__(self, error: SyntaxError) -> None:
        super().__init__(error.mensagem)
        self.error = error


class Parser:
    """Analisa tokens com linhas/colunas, sem alterar a saída do scanner."""

    def __init__(self, tokens: Sequence[Token]) -> None:
        self.tokens = tokens
        self.index = 0
        self.expression_depth = 0
        self.block_depth = 0

    def parse(self) -> Node:
        if not self.tokens:
            return self._node(
                "PROGRAMA",
                None,
                None,
                [],
                "programa ::= { comando }",
            )

        first = self._current()
        if first is not None and first.coluna != 1:
            self._fail(
                first,
                ["comando sem indentação"],
                "Uma instrução no nível principal não pode começar indentada.",
            )

        statements = self._parse_block(1)
        if self.index < len(self.tokens):
            token = self._current()
            self._fail(token, ["comando no nível principal"])

        return self._node(
            "PROGRAMA",
            statements[0] if statements else None,
            statements[-1] if statements else None,
            statements,
            "programa ::= { comando }",
        )

    def _parse_block(self, indentation: int) -> list[Node]:
        statements: list[Node] = []
        self.block_depth += 1
        if self.block_depth > MAX_NESTING_DEPTH:
            self.block_depth -= 1
            self._fail(
                self._current(),
                ["bloco com profundidade menor"],
                f"O aninhamento de blocos excede o limite de {MAX_NESTING_DEPTH}.",
            )

        try:
            while self.index < len(self.tokens):
                token = self._current()
                if token is None or token.coluna < indentation:
                    break
                if token.coluna > indentation:
                    self._fail(
                        token,
                        [f"instrução alinhada na coluna {indentation}"],
                        "A indentação não corresponde ao nível atual do bloco.",
                    )

                if token.lexema == "else":
                    self._fail(
                        token,
                        ["instrução dentro de um if correspondente"],
                        "A palavra 'else' não possui um 'if' correspondente neste nível.",
                    )
                if token.lexema == "if":
                    statements.append(self._parse_if(indentation))
                else:
                    statements.extend(self._parse_simple_line())
        finally:
            self.block_depth -= 1

        return statements

    def _parse_simple_line(self) -> list[Node]:
        statements: list[Node] = []
        first_token = self._current()
        if first_token is None:
            return statements
        line = first_token.linha

        while True:
            token = self._current()
            if token is None or token.linha != line:
                break
            if token.tipo == "IDENTIFICADOR":
                statements.append(self._parse_assignment())
            else:
                self._fail(
                    token,
                    ["identificador para iniciar uma atribuição", "if"],
                    "O subconjunto atual aceita atribuições e condicionais.",
                )

            next_token = self._current()
            if next_token is None or next_token.linha != line:
                break
            if next_token.lexema != ";":
                self._fail(
                    next_token,
                    ["fim da linha", "';'"],
                    "Separe instruções na mesma linha com ';' ou inicie uma nova linha.",
                )
            self.index += 1
            next_token = self._current()
            if next_token is None or next_token.linha != line:
                break

        return statements

    def _parse_assignment(self) -> Node:
        name = self._advance()
        if name is None:
            self._fail(None, ["identificador"])
        operator = self._current()
        if operator is None or operator.lexema != "=":
            self._fail(
                operator,
                ["'='"],
                "Era esperado '=' depois do identificador da atribuição.",
            )
        self.index += 1
        value = self._parse_expression()
        return self._node(
            "ATRIBUICAO",
            name,
            value,
            [value],
            "atribuicao ::= IDENTIFICADOR '=' expressao",
            {"nome": name.lexema, "operador": "="},
        )

    def _parse_if(self, indentation: int) -> Node:
        start = self._advance()
        if start is None:
            self._fail(None, ["'if'"])
        condition = self._parse_expression()
        colon = self._current()
        if colon is None or colon.lexema != ":":
            self._fail(
                colon,
                ["':'"],
                "Era esperado ':' ao final da condição do if.",
            )
        self.index += 1
        if self._current() is not None and self._current().linha == colon.linha:
            self._fail(
                self._current(),
                ["nova linha indentada"],
                "O bloco do if deve começar em uma nova linha indentada.",
            )

        first_body_token = self._current()
        if first_body_token is None or first_body_token.coluna <= indentation:
            self._fail(
                first_body_token,
                ["bloco indentado"],
                "Era esperado ao menos um comando indentado dentro do if.",
            )
        body_indentation = first_body_token.coluna
        body_statements = self._parse_block(body_indentation)
        if not body_statements:
            self._fail(
                self._current(),
                ["comando indentado"],
                "O bloco do if não pode estar vazio.",
            )
        body = self._block_node(body_statements)
        children = [condition, body]
        end_node = body

        token = self._current()
        if token is not None and token.lexema == "else" and token.coluna == indentation:
            self.index += 1
            else_colon = self._current()
            if else_colon is None or else_colon.lexema != ":":
                self._fail(else_colon, ["':'"], "Era esperado ':' depois de 'else'.")
            self.index += 1
            if self._current() is not None and self._current().linha == else_colon.linha:
                self._fail(
                    self._current(),
                    ["nova linha indentada"],
                    "O bloco do else deve começar em uma nova linha indentada.",
                )
            first_else_token = self._current()
            if first_else_token is None or first_else_token.coluna <= indentation:
                self._fail(
                    first_else_token,
                    ["bloco indentado"],
                    "Era esperado ao menos um comando indentado dentro do else.",
                )
            else_statements = self._parse_block(first_else_token.coluna)
            if not else_statements:
                self._fail(
                    self._current(),
                    ["comando indentado"],
                    "O bloco do else não pode estar vazio.",
                )
            end_node = self._block_node(else_statements)
            children.append(end_node)

        return self._node(
            "CONDICIONAL",
            start,
            end_node,
            children,
            "condicional ::= 'if' expressao ':' bloco [ 'else' ':' bloco ]",
        )

    def _parse_expression(self) -> Node:
        self.expression_depth += 1
        if self.expression_depth > MAX_NESTING_DEPTH:
            self.expression_depth -= 1
            self._fail(
                self._current(),
                ["expressão com profundidade menor"],
                f"O aninhamento de expressões excede o limite de {MAX_NESTING_DEPTH}.",
            )
        try:
            return self._parse_or()
        finally:
            self.expression_depth -= 1

    def _parse_or(self) -> Node:
        node = self._parse_and()
        while self._match_lexeme("or"):
            operator = self.tokens[self.index - 1]
            right = self._parse_and()
            node = self._binary_node("OU_LOGICO", operator, node, right, "expressao ::= expressao 'or' expressao_and")
        return node

    def _parse_and(self) -> Node:
        node = self._parse_not()
        while self._match_lexeme("and"):
            operator = self.tokens[self.index - 1]
            right = self._parse_not()
            node = self._binary_node("E_LOGICO", operator, node, right, "expressao_and ::= expressao_and 'and' expressao_not")
        return node

    def _parse_not(self) -> Node:
        if self._match_lexeme("not"):
            operator = self.tokens[self.index - 1]
            operand = self._parse_not()
            return self._unary_node("NEGACAO_LOGICA", operator, operand, "expressao_not ::= 'not' expressao_not")
        return self._parse_comparison()

    def _parse_comparison(self) -> Node:
        node = self._parse_addition()
        comparisons = {"==", "!=", "<", "<=", ">", ">="}
        if self._current() is not None and self._current().lexema in comparisons:
            operator = self._advance()
            right = self._parse_addition()
            node = self._binary_node("COMPARACAO", operator, node, right, "comparacao ::= expressao_soma operador_comparacao expressao_soma")
            if self._current() is not None and self._current().lexema in comparisons:
                self._fail(
                    self._current(),
                    ["operador lógico 'and'/'or' ou fim da expressão"],
                    "Comparações encadeadas não fazem parte do subconjunto suportado.",
                )
        return node

    def _parse_addition(self) -> Node:
        node = self._parse_multiplication()
        while self._current() is not None and self._current().lexema in {"+", "-"}:
            operator = self._advance()
            right = self._parse_multiplication()
            node_type = "SOMA" if operator.lexema == "+" else "SUBTRACAO"
            node = self._binary_node(node_type, operator, node, right, "expressao_soma ::= expressao_soma ('+' | '-') expressao_mult")
        return node

    def _parse_multiplication(self) -> Node:
        node = self._parse_unary()
        while self._current() is not None and self._current().lexema in {"*", "/", "//", "%"}:
            operator = self._advance()
            right = self._parse_unary()
            node_types = {"*": "MULTIPLICACAO", "/": "DIVISAO", "//": "DIVISAO_INTEIRA", "%": "RESTO"}
            node = self._binary_node(node_types[operator.lexema], operator, node, right, "expressao_mult ::= expressao_mult ('*' | '/' | '//' | '%') expressao_unaria")
        return node

    def _parse_unary(self) -> Node:
        if self._current() is not None and self._current().lexema in {"+", "-"}:
            operator = self._advance()
            operand = self._parse_unary()
            node_type = "POSITIVO_UNARIO" if operator.lexema == "+" else "NEGATIVO_UNARIO"
            return self._unary_node(node_type, operator, operand, "expressao_unaria ::= ('+' | '-') expressao_unaria")

        node = self._parse_primary()
        if self._match_lexeme("**"):
            operator = self.tokens[self.index - 1]
            right = self._parse_unary()
            return self._binary_node("POTENCIA", operator, node, right, "expressao_potencia ::= primaria '**' expressao_unaria")
        return node

    def _parse_primary(self) -> Node:
        token = self._current()
        if token is None:
            self._fail(None, ["expressão"])

        if token.lexema == "(":
            opening = self._advance()
            expression = self._parse_expression()
            closing = self._current()
            if closing is None or closing.lexema != ")":
                self._fail(
                    closing,
                    ["')'"],
                    "Era esperado ')' para fechar a expressão entre parênteses.",
                )
            self.index += 1
            return self._node(
                "AGRUPAMENTO",
                opening,
                closing,
                [expression],
                "primaria ::= '(' expressao ')'",
            )

        if token.tipo == "IDENTIFICADOR":
            self.index += 1
            return self._node(
                "IDENTIFICADOR",
                token,
                token,
                [],
                "primaria ::= IDENTIFICADOR",
                {"nome": token.lexema},
            )

        literal_types = {
            "LITERAL_INTEIRO": "LITERAL_INTEIRO",
            "LITERAL_REAL": "LITERAL_REAL",
            "LITERAL_STRING": "LITERAL_STRING",
        }
        if token.tipo in literal_types:
            self.index += 1
            return self._node(
                literal_types[token.tipo],
                token,
                token,
                [],
                "primaria ::= LITERAL",
                {"valor": token.lexema},
            )
        if token.tipo == "PALAVRA_RESERVADA" and token.lexema in {"True", "False"}:
            self.index += 1
            return self._node(
                "LITERAL_BOOLEANO",
                token,
                token,
                [],
                "primaria ::= 'True' | 'False'",
                {"valor": token.lexema},
            )
        if token.tipo == "PALAVRA_RESERVADA" and token.lexema == "None":
            self.index += 1
            return self._node(
                "LITERAL_NULO",
                token,
                token,
                [],
                "primaria ::= 'None'",
                {"valor": token.lexema},
            )
        self._fail(token, ["identificador", "literal", "'('"])

    def _block_node(self, statements: list[Node]) -> Node:
        return self._node(
            "BLOCO",
            statements[0],
            statements[-1],
            statements,
            "bloco ::= INDENT { comando } DEDENT",
        )

    def _binary_node(
        self,
        tipo: str,
        operator: Token,
        left: Node,
        right: Node,
        rule: str,
    ) -> Node:
        return self._node(
            tipo,
            left,
            right,
            [left, right],
            rule,
            {"operador": operator.lexema},
        )

    def _unary_node(self, tipo: str, operator: Token, operand: Node, rule: str) -> Node:
        return self._node(
            tipo,
            operator,
            operand,
            [operand],
            rule,
            {"operador": operator.lexema},
        )

    def _node(
        self,
        tipo: str,
        start: Token | Node | None,
        end: Token | Node | None,
        children: list[Node],
        rule: str,
        attributes: dict[str, object] | None = None,
    ) -> Node:
        if isinstance(start, Token):
            line, column = start.linha, start.coluna
        elif isinstance(start, Node):
            line, column = start.linha, start.coluna
        else:
            line, column = 1, 1

        if isinstance(end, Token):
            end_line = end.linha
            end_column = end.coluna + len(end.lexema) - 1
        elif isinstance(end, Node):
            end_line, end_column = end.linha_fim, end.coluna_fim
        else:
            end_line, end_column = line, column

        return Node(
            tipo,
            line,
            column,
            end_line,
            end_column,
            attributes or {},
            children,
            rule,
        )

    def _match_lexeme(self, lexeme: str) -> bool:
        if self._current() is not None and self._current().lexema == lexeme:
            self.index += 1
            return True
        return False

    def _advance(self) -> Token | None:
        token = self._current()
        if token is not None:
            self.index += 1
        return token

    def _current(self) -> Token | None:
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def _fail(
        self,
        token: Token | None,
        expected: list[str],
        detail: str | None = None,
    ) -> NoReturn:
        line = token.linha if token is not None else (self.tokens[-1].linha if self.tokens else 1)
        column = token.coluna if token is not None else (
            self.tokens[-1].coluna + len(self.tokens[-1].lexema) if self.tokens else 1
        )
        found = f"'{token.lexema}'" if token is not None else "fim do código"
        if detail is not None:
            message = f"Erro sintático na linha {line}, coluna {column}: {detail} Encontrado {found}."
        elif token is None:
            message = (
                f"Erro sintático na linha {line}, coluna {column}: "
                f"o código terminou antes da construção ser concluída; era esperado {', '.join(expected)}."
            )
        else:
            message = (
                f"Erro sintático na linha {line}, coluna {column}: "
                f"era esperado {', '.join(expected)}, mas foi encontrado {found}."
            )
        raise ParseFailure(SyntaxError(line, column, found, expected, message))


def parse(tokens: Sequence[Token]) -> tuple[dict[str, object] | None, list[dict[str, object]]]:
    """Retorna AST serializável e, se necessário, o primeiro erro sintático."""
    try:
        ast = Parser(tokens).parse()
    except ParseFailure as failure:
        return None, [failure.error.as_dict()]
    except RecursionError:
        last_token = tokens[-1] if tokens else None
        error = SyntaxError(
            last_token.linha if last_token else 1,
            last_token.coluna if last_token else 1,
            "fim da expressão",
            [f"aninhamento menor que {MAX_NESTING_DEPTH}"],
            f"O código excede a profundidade máxima de análise ({MAX_NESTING_DEPTH}).",
        )
        return None, [error.as_dict()]
    return ast.as_dict(), []
