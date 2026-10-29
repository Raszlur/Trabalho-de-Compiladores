import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "backend"))
from scanner import scan


class ScannerTestCase(unittest.TestCase):
    def test_scans_keywords_identifiers_literals_and_positions(self):
        tokens, errors = scan("if numero >= 10:\n    resultado = 'ok'")
        self.assertEqual(errors, [])
        self.assertEqual(
            [(token["tipo"], token["lexema"]) for token in tokens],
            [
                ("PALAVRA_RESERVADA", "if"),
                ("IDENTIFICADOR", "numero"),
                ("OPERADOR", ">="),
                ("LITERAL_INTEIRO", "10"),
                ("DELIMITADOR", ":"),
                ("IDENTIFICADOR", "resultado"),
                ("OPERADOR", "="),
                ("LITERAL_STRING", "'ok'"),
            ],
        )
        self.assertEqual((tokens[0]["linha"], tokens[0]["coluna"]), (1, 1))
        self.assertEqual((tokens[-1]["linha"], tokens[-1]["coluna"]), (2, 17))

    def test_scans_real_operators_delimiters_and_comments(self):
        tokens, errors = scan("valor = 3.14 + 2 # comentário\n# ignorado\nx != 0")
        self.assertEqual(errors, [])
        self.assertEqual(
            [token["lexema"] for token in tokens],
            ["valor", "=", "3.14", "+", "2", "x", "!=", "0"],
        )
        self.assertEqual(tokens[2]["tipo"], "LITERAL_REAL")

    def test_accumulates_invalid_character_and_unclosed_string_errors(self):
        tokens, errors = scan("x = @\ny = 'sem fim")
        self.assertEqual([token["lexema"] for token in tokens], ["x", "=", "y", "="])
        self.assertEqual(len(errors), 2)
        self.assertEqual((errors[0]["linha"], errors[0]["coluna"]), (1, 5))
        self.assertIn("não reconhecido", errors[0]["mensagem"])
        self.assertEqual((errors[1]["linha"], errors[1]["coluna"]), (2, 5))

    def test_ignores_whitespace_and_comments_at_end_of_file(self):
        self.assertEqual(scan("  # comentário sem quebra\n\t"), ([], []))


if __name__ == "__main__":
    unittest.main()
