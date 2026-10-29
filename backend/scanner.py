"""Scanner léxico para o subconjunto educacional de Python."""

from dataclasses import asdict, dataclass


KEYWORDS = {
    "and",
    "else",
    "False",
    "for",
    "if",
    "in",
    "None",
    "not",
    "or",
    "return",
    "True",
    "while",
}

TWO_CHARACTER_OPERATORS = {"==", "!=", "<=", ">=", "//", "**", "+=", "-=", "*=", "/="}
ONE_CHARACTER_OPERATORS = {"+", "-", "*", "/", "%", "=", ">", "<"}
DELIMITERS = {"(", ")", "[", "]", "{", "}", ",", ";", ":", "."}


@dataclass(frozen=True)
class Token:
    tipo: str
    lexema: str
    linha: int
    coluna: int

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LexicalError:
    tipo: str
    lexema: str
    linha: int
    coluna: int
    mensagem: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class Scanner:
    """Converte o código-fonte em tokens sem fazer análise sintática."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.index = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []
        self.errors: list[LexicalError] = []

    def scan(self) -> tuple[list[Token], list[LexicalError]]:
        while not self._at_end():
            character = self._peek()

            if character in " \t\r":
                self._advance()
            elif character == "\n":
                self._advance()
            elif character == "#":
                self._skip_comment()
            elif character.isalpha() or character == "_":
                self._scan_identifier()
            elif character.isdigit():
                self._scan_number()
            elif character in "'\"":
                self._scan_string()
            else:
                self._scan_operator_or_delimiter()

        return self.tokens, self.errors

    def _scan_identifier(self) -> None:
        line, column = self.line, self.column
        start = self.index
        while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()
        lexeme = self.source[start : self.index]
        tipo = "PALAVRA_RESERVADA" if lexeme in KEYWORDS else "IDENTIFICADOR"
        self.tokens.append(Token(tipo, lexeme, line, column))

    def _scan_number(self) -> None:
        line, column = self.line, self.column
        start = self.index
        while not self._at_end() and self._peek().isdigit():
            self._advance()

        tipo = "LITERAL_INTEIRO"
        if not self._at_end() and self._peek() == ".":
            if self._peek_next().isdigit():
                tipo = "LITERAL_REAL"
                self._advance()
                while not self._at_end() and self._peek().isdigit():
                    self._advance()
            else:
                self._add_error(
                    ".",
                    line,
                    self.column,
                    "Sequência numérica inválida: um ponto deve ser seguido por dígitos.",
                )
                self._advance()

        if not self._at_end() and (self._peek().isalpha() or self._peek() == "_"):
            while not self._at_end() and (self._peek().isalnum() or self._peek() == "_"):
                self._advance()
            lexeme = self.source[start : self.index]
            self._add_error(
                lexeme,
                line,
                column,
                f"Literal numérico inválido: '{lexeme}'.",
            )
            return

        self.tokens.append(Token(tipo, self.source[start : self.index], line, column))

    def _scan_string(self) -> None:
        line, column = self.line, self.column
        quote = self._advance()
        start = self.index - 1

        while not self._at_end() and self._peek() not in (quote, "\n"):
            if self._peek() == "\\":
                self._advance()
                if not self._at_end():
                    self._advance()
            else:
                self._advance()

        if self._at_end() or self._peek() == "\n":
            lexeme = self.source[start : self.index]
            self._add_error(
                lexeme,
                line,
                column,
                "String não fechada antes do fim da linha.",
            )
            return

        self._advance()
        self.tokens.append(Token("LITERAL_STRING", self.source[start : self.index], line, column))

    def _scan_operator_or_delimiter(self) -> None:
        line, column = self.line, self.column
        two_characters = self.source[self.index : self.index + 2]
        if two_characters in TWO_CHARACTER_OPERATORS:
            self._advance()
            self._advance()
            self.tokens.append(Token("OPERADOR", two_characters, line, column))
            return

        character = self._peek()
        if character in ONE_CHARACTER_OPERATORS:
            self._advance()
            self.tokens.append(Token("OPERADOR", character, line, column))
        elif character in DELIMITERS:
            self._advance()
            self.tokens.append(Token("DELIMITADOR", character, line, column))
        else:
            self._add_error(
                character,
                line,
                column,
                f"Caractere não reconhecido: '{character}'.",
            )
            self._advance()

    def _skip_comment(self) -> None:
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _add_error(self, lexeme: str, line: int, column: int, message: str) -> None:
        self.errors.append(LexicalError("ERRO_LEXICO", lexeme, line, column, message))

    def _peek(self) -> str:
        return "\0" if self._at_end() else self.source[self.index]

    def _peek_next(self) -> str:
        return "\0" if self.index + 1 >= len(self.source) else self.source[self.index + 1]

    def _advance(self) -> str:
        character = self.source[self.index]
        self.index += 1
        if character == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return character

    def _at_end(self) -> bool:
        return self.index >= len(self.source)


def scan(source: str) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    tokens, errors = Scanner(source).scan()
    return [token.as_dict() for token in tokens], [error.as_dict() for error in errors]
