import pathlib
import unittest


ROOT = pathlib.Path(__file__).parents[1]


class FrontendContractTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "frontend" / "src" / "index.html").read_text(encoding="utf-8")
        cls.javascript = (ROOT / "frontend" / "src" / "app.js").read_text(encoding="utf-8")

    def test_interface_contains_required_controls(self):
        for element_id in (
            "source-code",
            "example-select",
            "analyze-button",
            "result",
            "token-table-body",
            "lexical-errors",
            "syntax-errors",
            "syntax-status",
            "ast-tree",
            "ai-question",
            "ai-question-button",
            "ai-response",
            "expand-ast",
            "collapse-ast",
            "download-ast",
        ):
            self.assertIn(f'id="{element_id}"', self.html)

    def test_three_examples_are_available(self):
        for example in ("variable", "arithmetic", "conditional"):
            self.assertIn(f'value="{example}"', self.html)
            self.assertIn(f"{example}:", self.javascript)

    def test_frontend_posts_json_and_handles_validation(self):
        self.assertIn('fetch("/api/analyze"', self.javascript)
        self.assertIn('JSON.stringify({ codigo })', self.javascript)
        self.assertIn("Informe um código-fonte antes", self.javascript)
        self.assertIn("Não foi possível comunicar com o servidor", self.javascript)
        self.assertIn("showAnalysis", self.javascript)

    def test_ast_and_contextual_ai_controls_are_integrated(self):
        self.assertIn('fetch("/api/ia/explicar"', self.javascript)
        self.assertIn('tipo: "token"', self.javascript)
        self.assertIn('tipo: "ast"', self.javascript)
        self.assertIn("renderAstNode", self.javascript)
        self.assertIn("setSelectionRange", self.javascript)
        self.assertIn("Baixar AST em JSON", self.html)


if __name__ == "__main__":
    unittest.main()
