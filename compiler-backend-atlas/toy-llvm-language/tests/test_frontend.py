from __future__ import annotations

import unittest

from kofumini.ast_nodes import BinaryExpr, ReturnStmt
from kofumini.errors import LexError, ParseError, TypeCheckError
from kofumini.lexer import lex
from kofumini.parser import parse
from kofumini.typecheck import check


class FrontendTests(unittest.TestCase):
    def test_lexer_tracks_location_and_skips_comment(self) -> None:
        tokens = lex("// note\nfn main() -> Int { return 0; }")
        self.assertEqual(tokens[0].kind, "FN")
        self.assertEqual((tokens[0].line, tokens[0].column), (2, 1))

    def test_precedence_multiplies_before_add(self) -> None:
        program = parse(lex("fn main() -> Int { return 1 + 2 * 3; }"))
        statement = program.functions[0].body[0]
        self.assertIsInstance(statement, ReturnStmt)
        self.assertIsInstance(statement.value, BinaryExpr)
        self.assertEqual(statement.value.op, "+")
        self.assertIsInstance(statement.value.right, BinaryExpr)
        self.assertEqual(statement.value.right.op, "*")

    def test_unknown_character_is_a_lex_error(self) -> None:
        with self.assertRaises(LexError):
            lex("fn main() -> Int { return @; }")

    def test_missing_semicolon_is_a_parse_error(self) -> None:
        with self.assertRaises(ParseError):
            parse(lex("fn main() -> Int { return 0 }"))

    def test_main_signature_is_checked(self) -> None:
        program = parse(lex("fn main(value: Int) -> Int { return value; }"))
        with self.assertRaisesRegex(TypeCheckError, "main must have signature"):
            check(program)


if __name__ == "__main__":
    unittest.main()

