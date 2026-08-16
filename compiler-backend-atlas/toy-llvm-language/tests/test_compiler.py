from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from kofumini.compiler import compile_source
from kofumini.errors import RuntimeTrap, TypeCheckError
from kofumini.interpreter import Interpreter


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def compile_example(name: str):
    path = EXAMPLES / name
    return compile_source(path.read_text(encoding="utf-8"), path.name)


class CompilerPipelineTests(unittest.TestCase):
    def test_hello_interpreter(self) -> None:
        compilation = compile_example("hello.kofu")
        result = Interpreter(compilation.kir).run_main()
        self.assertEqual(result.stdout, "42\n")
        self.assertEqual(result.return_value, 0)

    def test_if_expression_lowers_to_phi(self) -> None:
        compilation = compile_example("choose.kofu")
        kir = compilation.kir.render()
        self.assertIn("phi", kir)
        self.assertIn("br", compilation.llvm_ir)
        self.assertIn("phi i64", compilation.llvm_ir)
        result = Interpreter(compilation.kir).run_main()
        self.assertEqual(result.stdout, "42\n")

    def test_bool_function_call_keeps_i1_signature(self) -> None:
        compilation = compile_example("functions.kofu")
        self.assertIn("define i1 @kofu.fn.is_large(i64 %arg.value)", compilation.llvm_ir)
        self.assertIn("call i1 @kofu.fn.is_large(i64", compilation.llvm_ir)
        result = Interpreter(compilation.kir).run_main()
        self.assertEqual(result.stdout, "144\n")

    def test_short_circuit_skips_side_effects(self) -> None:
        compilation = compile_example("short_circuit.kofu")
        result = Interpreter(compilation.kir).run_main()
        self.assertEqual(result.stdout, "42\n")
        self.assertNotIn("999", result.stdout)

    def test_checked_overflow_traps_in_reference_interpreter(self) -> None:
        compilation = compile_example("overflow.kofu")
        with self.assertRaisesRegex(RuntimeTrap, "overflow"):
            Interpreter(compilation.kir).run_main()
        self.assertIn("llvm.sadd.with.overflow.i64", compilation.llvm_ir)

    def test_type_error_is_rejected_before_kir(self) -> None:
        path = EXAMPLES / "type_error.kofu"
        with self.assertRaisesRegex(TypeCheckError, "declared Int, got Bool"):
            compile_source(path.read_text(encoding="utf-8"), path.name)

    def test_generated_module_has_c_abi_entry_wrapper(self) -> None:
        compilation = compile_example("hello.kofu")
        self.assertIn("define i64 @kofu.fn.main()", compilation.llvm_ir)
        self.assertIn("define i32 @main()", compilation.llvm_ir)


@unittest.skipUnless(shutil.which("clang"), "clang is not installed")
class NativeLLVMTests(unittest.TestCase):
    def test_clang_accepts_and_runs_generated_ir(self) -> None:
        compilation = compile_example("choose.kofu")
        with tempfile.TemporaryDirectory(prefix="kofumini-test-") as directory:
            directory_path = Path(directory)
            llvm_file = directory_path / "program.ll"
            executable = directory_path / "program"
            llvm_file.write_text(compilation.llvm_ir, encoding="utf-8", newline="\n")
            subprocess.run(
                [shutil.which("clang"), str(llvm_file), "-O2", "-o", str(executable)],
                check=True,
                capture_output=True,
                text=True,
            )
            result = subprocess.run(
                [str(executable)], check=False, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "42\n")


if __name__ == "__main__":
    unittest.main()

