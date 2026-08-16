from __future__ import annotations

import json
import unittest

from kofumini.compiler import compile_source
from kofumini.errors import VerificationError
from kofumini.kir import (
    Block,
    Instruction,
    KIRFunction,
    KIRModule,
    KIRParam,
    Terminator,
    verify,
)


class KIRSerializationTests(unittest.TestCase):
    SOURCE = "fn main() -> Int { let x: Int = 40 + 2; return x; }"

    def test_canonical_serialization_and_hash_are_deterministic(self) -> None:
        first = compile_source(self.SOURCE).kir
        second = compile_source(self.SOURCE).kir
        self.assertEqual(first.canonical_bytes(), second.canonical_bytes())
        self.assertEqual(first.content_hash(), second.content_hash())
        self.assertEqual(first.function_hashes(), second.function_hashes())
        self.assertEqual(json.loads(first.canonical_json())["schema"], "kofumini.kir/v1")

    def test_semantic_change_changes_function_hash(self) -> None:
        first = compile_source(self.SOURCE).kir.function_hashes()["main"]
        second = compile_source(self.SOURCE.replace("40 + 2", "40 + 3")).kir.function_hashes()[
            "main"
        ]
        self.assertNotEqual(first, second)


class KIRVerifierTests(unittest.TestCase):
    def test_empty_module_is_rejected(self) -> None:
        with self.assertRaisesRegex(VerificationError, "module has no functions"):
            verify(KIRModule([]))

    def test_same_block_use_before_definition_is_rejected(self) -> None:
        function = KIRFunction(
            "f",
            (KIRParam("x", "Int", "%arg.x"),),
            "Int",
            [
                Block(
                    "entry",
                    [
                        Instruction("iadd.checked", "%v0", "Int", ("%v1", "%arg.x")),
                        Instruction("const", "%v1", "Int", attrs={"value": 1}),
                    ],
                    Terminator("return", ("%v0",)),
                )
            ],
        )
        with self.assertRaisesRegex(VerificationError, "use before definition"):
            verify(KIRModule([function]))

    def test_phi_must_cover_exact_cfg_predecessors(self) -> None:
        function = KIRFunction(
            "choose",
            (
                KIRParam("cond", "Bool", "%arg.cond"),
                KIRParam("value", "Int", "%arg.value"),
            ),
            "Int",
            [
                Block(
                    "entry",
                    terminator=Terminator("branch", ("%arg.cond", "left", "right")),
                ),
                Block("left", terminator=Terminator("jump", ("merge",))),
                Block("right", terminator=Terminator("jump", ("merge",))),
                Block(
                    "merge",
                    [
                        Instruction(
                            "phi",
                            "%result",
                            "Int",
                            attrs={"incoming": [("left", "%arg.value")]},
                        )
                    ],
                    Terminator("return", ("%result",)),
                ),
            ],
        )
        with self.assertRaisesRegex(VerificationError, "predecessor set"):
            verify(KIRModule([function]))

    def test_return_type_mismatch_is_rejected(self) -> None:
        function = KIRFunction(
            "f",
            (),
            "Int",
            [
                Block(
                    "entry",
                    [Instruction("const", "%value", "Bool", attrs={"value": True})],
                    Terminator("return", ("%value",)),
                )
            ],
        )
        with self.assertRaisesRegex(VerificationError, "expected Int"):
            verify(KIRModule([function]))


if __name__ == "__main__":
    unittest.main()
