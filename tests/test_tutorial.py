from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from tutorial.stage1_calc import Parser as CalcParser
from tutorial.stage1_calc import evaluate as calc_evaluate
from tutorial.stage1_calc import lex as calc_lex

ROOT = Path(__file__).resolve().parents[1]
TUTORIAL = ROOT / "tutorial"


def run_stage(stage: str, example: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TUTORIAL / stage), str(TUTORIAL / "examples" / example)],
        text=True,
        capture_output=True,
        check=False,
    )


class TutorialTests(unittest.TestCase):
    def test_tree_checker_and_vm_agree_on_fibonacci(self) -> None:
        results = [
            run_stage("stage3_functions.py", "fib.mini"),
            run_stage("stage4_typecheck.py", "fib.mini"),
            run_stage("stage5_bytecode.py", "fib.mini"),
        ]
        for result in results:
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({result.stdout for result in results}, {results[0].stdout})

    def test_vm_preserves_lexical_shadowing(self) -> None:
        tree = run_stage("stage3_functions.py", "block_shadowing.mini")
        bytecode = run_stage("stage5_bytecode.py", "block_shadowing.mini")
        self.assertEqual(tree.returncode, 0, tree.stderr)
        self.assertEqual(bytecode.returncode, 0, bytecode.stderr)
        self.assertEqual(tree.stdout, "20\n10\n")
        self.assertEqual(bytecode.stdout, tree.stdout)

    def test_zero_argument_call_does_not_consume_outer_operand(self) -> None:
        tree = run_stage("stage3_functions.py", "zero_arg_call.mini")
        bytecode = run_stage("stage5_bytecode.py", "zero_arg_call.mini")
        self.assertEqual(tree.returncode, 0, tree.stderr)
        self.assertEqual(bytecode.returncode, 0, bytecode.stderr)
        self.assertEqual(tree.stdout, "42\n")
        self.assertEqual(bytecode.stdout, tree.stdout)

    def test_large_integer_division_never_round_trips_through_float(self) -> None:
        source = "100000000000000000000000000000000000001 / 3"
        ast = CalcParser(calc_lex(source)).parse_expr()
        self.assertEqual(calc_evaluate(ast), 33333333333333333333333333333333333333)

    def test_stage4_rejects_integer_condition(self) -> None:
        result = run_stage("stage4_typecheck.py", "bad_int_condition.mini")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("if condition must be bool", result.stderr)


if __name__ == "__main__":
    unittest.main()
