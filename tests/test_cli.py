from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from kofumini.cli import main


class CLITests(unittest.TestCase):
    def invoke(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(list(args))
        return status, stdout.getvalue(), stderr.getvalue()

    def test_tokens_stops_after_lexing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kofumini-cli-") as directory:
            source = Path(directory) / "incomplete.kofu"
            source.write_text("fn", encoding="utf-8")
            status, stdout, stderr = self.invoke("tokens", str(source))

        self.assertEqual(status, 0)
        self.assertIn("FN", stdout)
        self.assertEqual(stderr, "")

    def test_ast_stops_before_typechecking(self) -> None:
        text = "fn main(value: Int) -> Int { return value; }"
        with tempfile.TemporaryDirectory(prefix="kofumini-cli-") as directory:
            source = Path(directory) / "wrong-main.kofu"
            source.write_text(text, encoding="utf-8")
            ast_status, ast_stdout, ast_stderr = self.invoke("ast", str(source))
            check_status, _, check_stderr = self.invoke("check", str(source))

        self.assertEqual(ast_status, 0)
        self.assertIn('"node": "Program"', ast_stdout)
        self.assertEqual(ast_stderr, "")
        self.assertEqual(check_status, 1)
        self.assertIn("main must have signature", check_stderr)

    def test_llvm_output_creates_parent_directory(self) -> None:
        text = "fn main() -> Int { return 0; }"
        with tempfile.TemporaryDirectory(prefix="kofumini-cli-") as directory:
            root = Path(directory)
            source = root / "main.kofu"
            output = root / "generated" / "main.ll"
            source.write_text(text, encoding="utf-8")
            status, _, stderr = self.invoke("llvm", str(source), "-o", str(output))
            generated = output.read_text(encoding="utf-8")

        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        self.assertIn("define i32 @main()", generated)


if __name__ == "__main__":
    unittest.main()
