import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "backend"))
from parser import parse
from scanner import Scanner


def parse_source(source):
    tokens, lexical_errors = Scanner(source).scan()
    if lexical_errors:
        raise AssertionError(f"Entrada de teste contém erros léxicos: {lexical_errors}")
    return parse(tokens)


class ParserTestCase(unittest.TestCase):
    def test_parses_assignments_and_preserves_source_positions(self):
        ast, errors = parse_source("resultado = 10 + 5")
        self.assertEqual(errors, [])
        self.assertEqual(ast["tipo"], "PROGRAMA")
        assignment = ast["filhos"][0]
        self.assertEqual(assignment["tipo"], "ATRIBUICAO")
        self.assertEqual(assignment["atributos"]["nome"], "resultado")
        self.assertEqual((assignment["linha"], assignment["coluna"]), (1, 1))
        self.assertEqual((assignment["linhaFim"], assignment["colunaFim"]), (1, 18))

    def test_operator_precedence_and_left_associativity(self):
        ast, errors = parse_source("x = 2 + 3 * 4\ny = 10 - 3 - 2\nz = (10 + 5) * 2")
        self.assertEqual(errors, [])
        first_expression = ast["filhos"][0]["filhos"][0]
        self.assertEqual(first_expression["tipo"], "SOMA")
        self.assertEqual(first_expression["filhos"][1]["tipo"], "MULTIPLICACAO")

        second_expression = ast["filhos"][1]["filhos"][0]
        self.assertEqual(second_expression["tipo"], "SUBTRACAO")
        self.assertEqual(second_expression["filhos"][0]["tipo"], "SUBTRACAO")

        third_expression = ast["filhos"][2]["filhos"][0]
        self.assertEqual(third_expression["tipo"], "MULTIPLICACAO")
        self.assertEqual(third_expression["filhos"][0]["tipo"], "AGRUPAMENTO")

    def test_parses_boolean_conditions_and_nested_if_else_blocks(self):
        source = (
            "numero = 10\n"
            "if numero > 0 and not False:\n"
            "    if numero == 10:\n"
            "        resultado = numero ** 2\n"
            "    else:\n"
            "        resultado = 1\n"
            "else:\n"
            "    resultado = 0\n"
        )
        ast, errors = parse_source(source)
        self.assertEqual(errors, [])
        conditional = ast["filhos"][1]
        self.assertEqual(conditional["tipo"], "CONDICIONAL")
        self.assertEqual(len(conditional["filhos"]), 3)
        self.assertEqual(conditional["filhos"][0]["tipo"], "E_LOGICO")
        nested_if = conditional["filhos"][1]["filhos"][0]
        self.assertEqual(nested_if["tipo"], "CONDICIONAL")
        self.assertEqual(nested_if["filhos"][1]["filhos"][0]["tipo"], "ATRIBUICAO")
        self.assertEqual(nested_if["filhos"][2]["tipo"], "BLOCO")

    def test_parses_semicolon_separated_statements_and_empty_program(self):
        ast, errors = parse_source("x = 1; y = 2\n")
        self.assertEqual(errors, [])
        self.assertEqual([node["atributos"]["nome"] for node in ast["filhos"]], ["x", "y"])
        empty_ast, empty_errors = parse_source("")
        self.assertEqual(empty_errors, [])
        self.assertEqual(empty_ast["filhos"], [])
        comment_ast, comment_errors = parse_source("# somente comentário")
        self.assertEqual(comment_errors, [])
        self.assertEqual(comment_ast["filhos"], [])

    def test_reports_missing_colon_and_missing_expression_with_location(self):
        for source, expected, line, column in (
            ("if x > 0\n    y = 1", ["':'"], 2, 5),
            ("x = 1 +", ["expressão"], 1, 8),
        ):
            with self.subTest(source=source):
                ast, errors = parse_source(source)
                self.assertIsNone(ast)
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[0]["tipo"], "ERRO_SINTATICO")
                self.assertEqual(errors[0]["esperado"], expected)
                self.assertEqual((errors[0]["linha"], errors[0]["coluna"]), (line, column))
                self.assertIn("Erro sintático", errors[0]["mensagem"])

    def test_reports_unmatched_else_and_indentation_errors(self):
        for source in ("else:\n    x = 1", "if True:\nx = 1", "x = 1\n  y = 2"):
            with self.subTest(source=source):
                ast, errors = parse_source(source)
                self.assertIsNone(ast)
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[0]["tipo"], "ERRO_SINTATICO")

    def test_reports_unclosed_parentheses_and_rejects_chained_comparisons(self):
        for source in ("x = (1 + 2", "x = 1 < 2 < 3"):
            with self.subTest(source=source):
                ast, errors = parse_source(source)
                self.assertIsNone(ast)
                self.assertEqual(len(errors), 1)

    def test_accepts_basic_comparison_and_logical_operators(self):
        ast, errors = parse_source("x = 1 <= 2 or 3 != 4 and True")
        self.assertEqual(errors, [])
        self.assertEqual(ast["filhos"][0]["filhos"][0]["tipo"], "OU_LOGICO")


if __name__ == "__main__":
    unittest.main()
